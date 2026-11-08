# Guía de etiquetado – M1P1

## 1. Objetivo

Establecer criterios uniformes para clasificar las consultas de los usuarios del sistema de soporte.

Cada consulta debe recibir exactamente una categoría, seleccionada según la intención principal del usuario.

## 2. Categorías disponibles

- `billing`: facturación, pagos, cobros, reembolsos y métodos de pago.
- `technical`: problemas técnicos, errores de funcionamiento, fallas de acceso y dificultades operativas.
- `account`: gestión de cuentas, credenciales, información personal y configuración de usuario.
- `other`: consultas que no pertenecen a ninguna de las categorías anteriores o cuyo propósito no puede identificarse con suficiente información.

No se deben crear categorías nuevas.

## 3. Reglas de clasificación

### R01 – Gestión de credenciales

Las solicitudes relacionadas con la modificación, recuperación o administración de credenciales corresponden a `account`.

Ejemplos:
- Cambiar el correo electrónico asociado a la cuenta.
- Restablecer o modificar una contraseña.
- Actualizar información de acceso.

### R02 – Incidencias de facturación

Las consultas relacionadas con problemas económicos o administrativos de pagos corresponden a `billing`.

Ejemplos:
- Cobros incorrectos o excesivos.
- Cargos duplicados.
- Solicitudes de reembolso.
- Consultas sobre facturas o importes cobrados.

### R03 – Problemas técnicos de acceso

Cuando el usuario informa que no puede acceder al sistema debido a errores, fallas o problemas de funcionamiento, corresponde `technical`.

Ejemplos:
- Errores al iniciar sesión.
- Fallas del sistema de autenticación.
- Imposibilidad de acceder pese a utilizar credenciales válidas.

Si el usuario solicita explícitamente modificar o recuperar sus credenciales, se aplica R01.

### R04 – Administración de cuenta

Las solicitudes relacionadas con la consulta, modificación o eliminación de una cuenta corresponden a `account`.

Ejemplos:
- Consultar información de la cuenta.
- Modificar datos personales.
- Eliminar una cuenta.
- Consultar configuraciones del perfil.

### R05 – Administración de medios de pago

Las solicitudes relacionadas con agregar, eliminar o modificar métodos de pago corresponden a `billing`.

Ejemplos:
- Cambiar una tarjeta.
- Actualizar el medio de pago.
- Agregar una nueva forma de pago.
- Eliminar un método de pago registrado.

### R06 – Consultas fuera de dominio

Las consultas que no corresponden a facturación, problemas técnicos o gestión de cuenta deben clasificarse como `other`.

También se utiliza esta categoría cuando no existe información suficiente para identificar una intención concreta.

### R07 – Prioridad de la intención principal

Cuando una consulta contiene más de una solicitud o problema, debe prevalecer la intención principal del usuario.

La clasificación no debe depender exclusivamente de palabras clave, sino del objetivo que el usuario intenta alcanzar.

Si no es posible identificar una intención predominante, se utiliza `other`.

## 4. Criterios generales de etiquetado

1. Cada consulta recibe exactamente una categoría.
2. Se clasifica según la intención principal, no solamente por palabras clave.
3. El lenguaje informal, los errores ortográficos, los emojis y la puntuación no modifican por sí mismos la categoría.
4. No se deben inferir problemas que el usuario no haya mencionado.
5. Las reglas específicas R01–R06 prevalecen sobre una interpretación genérica de la consulta.
6. R07 se aplica cuando existen múltiples intenciones.
7. Ante falta de información suficiente, se utiliza `other`.
8. Las etiquetas deben utilizar exclusivamente los identificadores técnicos definidos en esta guía.

## 5. Registro de etiquetas

Cada consulta etiquetada debe registrar:

- `categoria`: categoría asignada.
- `regla`: código de la regla aplicada, cuando corresponda.
- `justificacion`: explicación breve de la decisión de clasificación.

Las etiquetas constituyen la referencia de evaluación (*ground truth*) para medir el desempeño del modelo.