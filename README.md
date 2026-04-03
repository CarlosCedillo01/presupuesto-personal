Finanzas Express - Simulador de Presupuesto Personal |
Finanzas Express es una plataforma integral de gestión financiera que fusiona la potencia del análisis de datos con una interfaz intuitiva. El sistema permite a los usuarios monitorear sus hábitos de consumo, establecer límites de gasto y visualizar proyecciones de ahorro inteligentes mediante una arquitectura cliente-servidor robusta.
Características Principales
•	Inteligencia Financiera: Implementación de la Regla 50/30/20 para asesorar al usuario sobre la distribución de sus ingresos (Necesidades, Deseos y Ahorro).
•	Proyección Algorítmica: Motor de cálculo que estima la fecha exacta de cumplimiento de metas basado en el ritmo de ahorro actual.
•	Gestión de Presupuestos: Configuración de límites mensuales por categoría con un sistema automático de alertas de sobregiro.
•	Seguridad de Datos: Autenticación de usuarios con hashing de contraseñas mediante PBKDF2. (Password-Based Key Derivation Function 2) o en español un algoritmo criptográfico estándar utilizado para convertir contraseñas en claves fuertes mediante el uso de "sal" (salt) e iteraciones intensivas. Al hacer lento el proceso de hashing (miles o cientos de miles de veces), protege las contraseñas contra ataques de fuerza bruta
•	Reportes y Exportación: Visualización de balances netos y capacidad de descargar el historial completo en formato CSV.
 Stack Tecnológico

•	| Backend: Python 3.10+ & Flask.
•	| Base de Datos: SQLite 3 (con integridad referencial y soft-delete).
•	| Frontend: JavaScript (ES6+), HTML5 y CSS3.
•	| Seguridad:  Werkzeug Security.
Estructura del Proyecto
/FINANZAS EXPRESS
├── app.py              # Servidor Flask y lógica de rutas (API)
├── database.py         # Gestión de BD, hashing y lógica de negocio
├── budget.db           # Base de datos SQLite (generada al iniciar)
├── .gitignore          # Archivos omitidos en el control de versiones
└── static/             # Archivos de la interfaz de usuario
    ├── index.html      # Dashboard principal
    ├── login.html      # Pantalla de acceso
    ├── styles.css      # Estilizado y UI Design
    └── app.js          # Lógica de cliente y consumo de API



Instalación y Ejecución
Sigue estos pasos para poner en marcha el simulador en tu entorno local:
1.	Clonar el repositorio: git clone [https://github.com/tu-usuario/presupuesto-personal.git](https://github.com/tu-usuario/presupuesto-personal.git)
cd presupuesto-personal
2.	Instalar dependencias: 
- Se requiere Flask y Werkzeug para el correcto funcionamiento del servidor: pip install flask werkzeug
3.	Iniciar la aplicación: python app.py
4.	Acceder al sistema: Abre tu navegador en http://localhost:XXXX Puedes usar las credenciales demo:
“Usuario: usuario01 | Clave: finanzas2024”
Documentación de la API (Endpoints)
Método	Endpoint	Funcionalidad
POST	/api/login	Autenticación y creación de sesión.
GET	/api/transactions	Obtención de movimientos filtrados por mes.
POST	/api/transactions	Registro de nuevos ingresos o gastos.
GET	/api/budgets	Consulta de límites presupuestarios.
GET	/api/savings	Estado de metas y proyecciones de ahorro.
GET	/api/report	Resumen ejecutivo con recomendaciones (Regla 50/30/20).
GET	/api/export/csv	Generación de archivo descargable.

Diseño y UX/UI
El diseño visual fue concebido para reducir la carga cognitiva al manejar datos financieros. Se priorizó una jerarquía visual clara, colores que facilitan la interpretación de estados (ahorro vs. gasto) y una navegación fluida mediante peticiones asíncronas que evitan recargas innecesarias de la página.
Créditos 
Proyecto desarrollado por: 
-Juan Mendez, 
-Carlos M. Santana, 
-Carlos Cedillo, 
-Iván O. Chavez, 
-Itzayana Aguilar 
