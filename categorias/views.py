from bson import ObjectId
from bson.errors import InvalidId

from django.contrib import messages
from django.shortcuts import render, redirect

from pymongo.errors import PyMongoError

from productos.db import coleccion_categorias, coleccion_productos


def validar_categoria(datos):
    """Valida los datos recibidos del formulario de categorías."""

    nombre = datos.get("nombre", "").strip()
    descripcion = datos.get("descripcion", "").strip()

    errores = []

    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif len(nombre) > 50:
        errores.append("El nombre no puede superar 50 caracteres.")

    if len(descripcion) > 200:
        errores.append("La descripción no puede superar 200 caracteres.")

    categoria = {
        "nombre": nombre,
        "descripcion": descripcion,
    }

    return categoria, errores


def listar(request):
    """Consulta y muestra las categorías."""

    try:
        datos = list(
            coleccion_categorias.find().sort("nombre", 1)
        )

        for categoria in datos:
            categoria["id"] = str(categoria["_id"])

        return render(
            request,
            "categorias/lista.html",
            {"categorias": datos},
        )

    except PyMongoError:
        messages.error(
            request,
            "No fue posible consultar las categorías. "
            "Verifica la conexión con MongoDB."
        )

        return render(
            request,
            "categorias/lista.html",
            {"categorias": []},
        )


def crear(request):
    """Registra una categoría."""

    if request.method == "POST":
        categoria, errores = validar_categoria(request.POST)

        if errores:
            for error in errores:
                messages.error(request, error)

            return render(
                request,
                "categorias/formulario.html",
                {"categoria": categoria},
            )

        try:
            coleccion_categorias.insert_one(categoria)

            messages.success(
                request,
                "Categoría registrada correctamente."
            )

            return redirect("categorias:listar")

        except PyMongoError:
            messages.error(
                request,
                "No fue posible guardar la categoría."
            )

            return render(
                request,
                "categorias/formulario.html",
                {"categoria": categoria},
            )

    return render(request, "categorias/formulario.html")


def editar(request, id):
    """Actualiza una categoría existente."""

    try:
        identificador = ObjectId(id)
    except (InvalidId, TypeError):
        messages.error(request, "El identificador no es válido.")
        return redirect("categorias:listar")

    try:
        categoria_actual = coleccion_categorias.find_one(
            {"_id": identificador}
        )

        if categoria_actual is None:
            messages.error(request, "La categoría no existe.")
            return redirect("categorias:listar")

        if request.method == "POST":
            categoria, errores = validar_categoria(request.POST)

            if errores:
                for error in errores:
                    messages.error(request, error)

                return render(
                    request,
                    "categorias/formulario.html",
                    {"categoria": categoria},
                )

            resultado = coleccion_categorias.update_one(
                {"_id": identificador},
                {"$set": categoria},
            )

            if resultado.matched_count == 0:
                messages.error(request, "La categoría ya no existe.")
            else:
                messages.success(
                    request,
                    "Categoría actualizada correctamente."
                )

            return redirect("categorias:listar")

        return render(
            request,
            "categorias/formulario.html",
            {"categoria": categoria_actual},
        )

    except PyMongoError:
        messages.error(
            request,
            "No fue posible consultar o actualizar la categoría."
        )

        return redirect("categorias:listar")


def eliminar(request, id):
    """Elimina una categoría mediante POST."""

    if request.method != "POST":
        messages.error(
            request,
            "La eliminación requiere enviar el formulario."
        )
        return redirect("categorias:listar")

    try:
        identificador = ObjectId(id)
    except (InvalidId, TypeError):
        messages.error(request, "El identificador no es válido.")
        return redirect("categorias:listar")

    try:
        # No se puede borrar una categoría que todavía tiene productos
        productos_en_uso = coleccion_productos.count_documents(
            {"categoria_id": identificador}
        )

        if productos_en_uso > 0:
            messages.error(
                request,
                "No se puede eliminar: hay productos en esta categoría."
            )
            return redirect("categorias:listar")

        resultado = coleccion_categorias.delete_one(
            {"_id": identificador}
        )

        if resultado.deleted_count == 1:
            messages.success(
                request,
                "Categoría eliminada correctamente."
            )
        else:
            messages.error(
                request,
                "La categoría no existe o ya fue eliminada."
            )

    except PyMongoError:
        messages.error(
            request,
            "No fue posible eliminar la categoría."
        )

    return redirect("categorias:listar")