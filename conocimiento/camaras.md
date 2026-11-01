# Cámaras IP y CCTV

## Cámara IP sin imagen o desconectada
1. Identifica si afecta una cámara o todas. Si son todas, revisa primero el grabador y el switch.
2. Verifica que el puerto del switch PoE tenga enlace y que la cámara reciba energía.
3. Comprueba el cable de red y sus conectores. Prueba la cámara en otro puerto.
4. Haz ping a la dirección IP de la cámara desde un equipo en la misma red.
5. Si responde al ping pero no da video, revisa en el grabador el canal, el usuario y el protocolo.
6. Si no responde al ping ni con otro cable y otro puerto, escala para revisión en sitio.

## Imagen borrosa, con ruido o manchas
1. Limpia el lente con un paño suave y sin químicos.
2. Revisa el enfoque y el zoom desde la interfaz de la cámara.
3. En la noche, verifica que los infrarrojos no se reflejen en un vidrio o en una pared cercana.
4. Reduce la exposición directa a luz o activa la función WDR si la cámara la soporta.

## Conflicto de direcciones IP
1. Síntoma típico: la cámara aparece y desaparece, o dos equipos responden a la misma IP.
2. Lista las direcciones en uso con la herramienta de búsqueda del fabricante.
3. Asigna una IP libre, fuera del rango DHCP del router.
4. Documenta la IP asignada en el inventario del cliente.
