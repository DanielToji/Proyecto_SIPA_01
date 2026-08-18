class Roles:
    """Identificadores de roles del sistema."""
    ADMIN = 1
    COORDINADOR = 2
    INSTRUCTOR = 3
    APRENDIZ = 4
    APOYO_ADMINISTRATIVO = 5
    CONSULTA = 6


class RolesPermisos:
    """Conjuntos de roles agrupados por nivel de acceso."""
    ESCRITURA = {Roles.ADMIN, Roles.COORDINADOR}
    LECTURA = {Roles.ADMIN, Roles.COORDINADOR, Roles.INSTRUCTOR, Roles.APRENDIZ}
    SEGUIMIENTO = {Roles.ADMIN, Roles.COORDINADOR, Roles.INSTRUCTOR}
    SOLO_ADMIN = {Roles.ADMIN}
    ADMIN_Y_COORDINADOR = {Roles.ADMIN, Roles.COORDINADOR}
    INSTRUCTOR_Y_COORDINADOR = {Roles.COORDINADOR, Roles.INSTRUCTOR}