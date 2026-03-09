
# Red Logística de Ayuda Humanitaria  

## Contexto del problema

Durante la temporada de lluvias en Colombia, el departamento de Córdoba experimenta inundaciones recurrentes debido al incremento del caudal del río Sinú. Estas inundaciones afectan tanto zonas urbanas como rurales, provocando daños en viviendas, afectaciones en la infraestructura vial, pérdida de cultivos y dificultades en el acceso a servicios básicos.

En situaciones de emergencia como estas, diferentes entidades gubernamentales y organizaciones humanitarias deben coordinar la distribución de ayuda hacia las comunidades afectadas. Esta ayuda incluye alimentos, agua potable, medicamentos, kits de higiene y otros recursos esenciales para la atención de la población damnificada.

Sin embargo, la distribución eficiente de estos recursos representa un desafío logístico importante. Las inundaciones pueden dañar carreteras, limitar el acceso a ciertas zonas y generar restricciones en el transporte de suministros. Además, las comunidades afectadas pueden encontrarse dispersas geográficamente, lo que dificulta la planificación de rutas de distribución eficientes.

Debido a estas dificultades, es necesario analizar cuidadosamente la red de transporte disponible para garantizar que la ayuda humanitaria llegue de manera oportuna a las zonas afectadas.

---

## Representación de la red logística

Para estudiar este problema, el sistema de distribución de ayuda humanitaria se representa mediante una **red logística**, modelada como un **grafo dirigido**.

En este modelo:

- Cada **nodo** representa un punto dentro del sistema logístico.
- Cada **arista** representa una ruta de transporte entre dos puntos.

Esta representación permite describir de manera estructurada el flujo de ayuda humanitaria desde los centros de abastecimiento hasta las comunidades afectadas.

---

## Centros de abastecimiento

Los nodos **1 y 2** representan los principales centros de acopio desde donde se despachan los suministros humanitarios.

En estos puntos se reciben recursos provenientes de diferentes entidades, como:

- organismos gubernamentales
- organizaciones humanitarias
- donaciones de instituciones y ciudadanos

Desde estos centros se organiza el envío de ayuda hacia diferentes puntos de la red logística.

---

## Centros logísticos intermedios

Los nodos **3 al 77** representan centros logísticos intermedios dentro de la red de distribución.

Estos nodos pueden corresponder a:

- bodegas regionales
- centros de redistribución
- puntos de almacenamiento temporal
- intersecciones importantes dentro de la red de transporte

Su función principal es facilitar la redistribución de los recursos dentro de la red, permitiendo que la ayuda pueda ser enviada hacia diferentes comunidades según las necesidades de cada zona.

---

## Zonas afectadas

Los nodos **78, 79 y 80** representan las comunidades o municipios afectados por las inundaciones donde finalmente se realiza la entrega de la ayuda humanitaria.

Estos nodos corresponden a los **puntos finales de la red logística**, donde los recursos llegan directamente a la población damnificada.

---

## Características de la red de transporte

Las conexiones entre nodos representan las rutas disponibles para transportar ayuda humanitaria entre diferentes puntos del territorio.

Estas rutas pueden corresponder a:

- carreteras principales
- vías secundarias
- caminos rurales que conectan municipios y comunidades

Cada conexión describe una posible vía por la cual pueden movilizarse los suministros dentro de la red logística.

---

## Propósito del proyecto

El propósito de este proyecto es analizar la estructura de la red logística utilizada para distribuir ayuda humanitaria durante situaciones de emergencia causadas por inundaciones en el departamento de Córdoba.

A partir de la representación de la red mediante grafos, es posible estudiar cómo se conectan los diferentes puntos del sistema logístico y comprender las rutas a través de las cuales se distribuyen los recursos destinados a las comunidades afectadas.

---

## Autores
- Samuel Eduardo Emperador Contreras
- Alejandra Abaunza Suárez
- Karla Mariana Martínez Cedeño
- Johann Sebastian Berrio Barreto

Proyecto académico desarrollado para la asignatura **Optimización y Simulación**.
