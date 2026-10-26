import math

from bson import ObjectId
from bson.errors import InvalidId

from django.contrib import messages
from django.shortcuts import render, redirect

from pymongo.errors import PyMongoError

from .db import coleccion_productos, coleccion_categorias


def obtener_categorias():
    """Devuelve las categorías con un campo id de tipo texto."""

    categorias = list(
        coleccion_categorias.find().sort("nombre", 1)
    )

    for categoria in categorias:
        categoria["id"] = str(categoria["_id"])

    return categorias


def mostrar_formulario(request, producto=None):
    """Muestra el formulario junto con la lista de categorías."""

    try:
        categorias = obtener_categorias()
    except PyMongoError:
        categorias = []
        messages.error(
            request,
            "No fue posible consultar las categorías."
        )

    return render(
        request,
        "productos/formulario.html",
        {"producto": producto, "categorias": categorias},
    )


def validar_producto(datos):
    """Valida los datos recibidos del formulario."""

    nombre = datos.get("nombre", "").strip()
    precio_texto = datos.get("precio", "").strip()
    cantidad_texto = datos.get("cantidad", "").strip()
    categoria_texto = datos.get("categoria_id", "").strip()

    errores = []

    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif len(nombre) > 100:
        errores.append("El nombre no puede superar 100 caracteres.")

    try:
        precio = float(precio_texto)

        if not math.isfinite(precio) or precio < 0:
            errores.append(
                "El precio debe ser un número válido y no negativo."
            )
    except ValueError:
        precio = None
        errores.append("Ingresa un precio válido.")

    try:
        cantidad = int(cantidad_texto)

        if cantidad < 0:
            errores.append("La cantidad no puede ser negativa.")
    except ValueError:
        cantidad = None
        errores.append("La cantidad debe ser un número entero.")

    try:
        categoria_id = ObjectId(categoria_texto)

        existe = coleccion_categorias.count_documents(
            {"_id": categoria_id}
        )

        if existe == 0:
            errores.append("La categoría seleccionada no existe.")
    except (InvalidId, TypeError):
        categoria_id = None
        errores.append("Selecciona una categoría.")
    except PyMongoError:
        categoria_id = None
        errores.append("No fue posible verificar la categoría.")

    producto = {
        "nombre": nombre,
        "precio": precio,
        "cantidad": cantidad,
        "categoria_id": categoria_id,
    }

    return producto, errores


def listar(request):
    """Consulta y muestra los productos."""

    try:
        datos = list(
            coleccion_productos.find().sort("nombre", 1)
        )

        nombres = {
            categoria["_id"]: categoria["nombre"]
            for categoria in coleccion_categorias.find()
        }

        for producto in datos:
            producto["id"] = str(producto["_id"])
            producto["categoria_nombre"] = nombres.get(
                producto.get("categoria_id"),
                "Sin categoría",
            )

        return render(
            request,
            "productos/lista.html",
            {"productos": datos},
        )

    except PyMongoError:
        messages.error(
            request,
            "No fue posible consultar los productos. "
            "Verifica la conexión con MongoDB."
        )

        return render(
            request,
            "productos/lista.html",
            {"productos": []},
        )


def crear(request):
    """Registra un producto."""

    if request.method == "POST":
        producto, errores = validar_producto(request.POST)

        if errores:
            for error in errores:
                messages.error(request, error)

            return mostrar_formulario(request, producto)

        try:
            coleccion_productos.insert_one(producto)

            messages.success(
                request,
                "Producto registrado correctamente."
            )

            return redirect("productos:listar")

        except PyMongoError:
            messages.error(
                request,
                "No fue posible guardar el producto."
            )

            return mostrar_formulario(request, producto)

    return mostrar_formulario(request)


def editar(request, id):
    """Actualiza un producto existente."""

    try:
        identificador = ObjectId(id)
    except (InvalidId, TypeError):
        messages.error(request, "El identificador no es válido.")
        return redirect("productos:listar")

    try:
        producto_actual = coleccion_productos.find_one(
            {"_id": identificador}
        )

        if producto_actual is None:
            messages.error(request, "El producto no existe.")
            return redirect("productos:listar")

        if request.method == "POST":
            producto, errores = validar_producto(request.POST)

            if errores:
                for error in errores:
                    messages.error(request, error)

                return mostrar_formulario(request, producto)

            resultado = coleccion_productos.update_one(
                {"_id": identificador},
                {"$set": producto},
            )

            if resultado.matched_count == 0:
                messages.error(request, "El producto ya no existe.")
            else:
                messages.success(
                    request,
                    "Producto actualizado correctamente."
                )

            return redirect("productos:listar")

        return mostrar_formulario(request, producto_actual)

    except PyMongoError:
        messages.error(
            request,
            "No fue posible consultar o actualizar el producto."
        )

        return redirect("productos:listar")


def eliminar(request, id):
    """Elimina un producto mediante POST."""

    if request.method != "POST":
        messages.error(
            request,
            "La eliminación requiere enviar el formulario."
        )
        return redirect("productos:listar")

    try:
        identificador = ObjectId(id)
    except (InvalidId, TypeError):
        messages.error(request, "El identificador no es válido.")
        return redirect("productos:listar")

    try:
        resultado = coleccion_productos.delete_one(
            {"_id": identificador}
        )

        if resultado.deleted_count == 1:
            messages.success(
                request,
                "Producto eliminado correctamente."
            )
        else:
            messages.error(
                request,
                "El producto no existe o ya fue eliminado."
            )

    except PyMongoError:
        messages.error(
            request,
            "No fue posible eliminar el producto."
        )

    return redirect("productos:listar")