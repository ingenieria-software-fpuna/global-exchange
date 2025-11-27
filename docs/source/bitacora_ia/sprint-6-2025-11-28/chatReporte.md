**Usuario:**  
Necesito implementar este nuevo requerimiento: Reporte de transacciones y Reporte de ganancias.  
Tienen que ser nuevas pantallas y cada una debe tener sus propios permisos.  
Los reportes deberán poder filtrarse por período de tiempo y tipo de transacción.  
Se podrá exportar en PDF o Excel.  
Se podrá visualizar un desglose de ganancias por tipo de moneda (USD, EUR, PYG, etc.) y global (PYG).

---

**Claude:**  
Perfecto. Ahora voy a crear la funcionalidad completa para los reportes.  
Necesito:

- Crear vistas para los reportes con filtros y exportación  
- Agregar permisos personalizados en el modelo  
- Crear templates para las pantallas de reportes  
- Agregar URLs para acceder a los reportes  
- Crear formularios para los filtros  

```python

def aplicar_filtros_transacciones(queryset, form_data):
    """
    Aplica filtros al queryset de transacciones según los datos del formulario.
    """
    fecha_desde = form_data.get('fecha_desde')
    fecha_hasta = form_data.get('fecha_hasta')
    tipo_operacion = form_data.get('tipo_operacion')
    estado = form_data.get('estado')
    moneda = form_data.get('moneda')
    cliente = form_data.get('cliente')
    usuario = form_data.get('usuario')
    
    # Aplicar filtros
    if fecha_desde:
        queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)
    
    if fecha_hasta:
        queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)
    
    if tipo_operacion:
        queryset = queryset.filter(tipo_operacion=tipo_operacion)
    
    if estado:
        queryset = queryset.filter(estado=estado)
    
    if moneda:
        queryset = queryset.filter(
            Q(moneda_origen=moneda) | Q(moneda_destino=moneda)
        )
    
    if cliente:
        queryset = queryset.filter(cliente=cliente)
    
    if usuario:
        queryset = queryset.filter(usuario=usuario)
    
    return queryset, fecha_desde, fecha_hasta


def calcular_ganancias_por_tipo(transacciones):
    """
    Calcula las ganancias por tipo de operación (Compra/Venta) en PYG.
    
    Args:
        transacciones: QuerySet de transacciones a procesar
        
    Returns:
        dict: Diccionario con estructura {codigo_tipo: {'tipo': TipoOperacion, 'ganancia_neta_pyg': Decimal, 
              'comisiones_pyg': Decimal, 'descuentos_pyg': Decimal, 'cantidad': int}}
    """
    ganancias_por_tipo = {}
    
    for tipo in TipoOperacion.objects.filter(activo=True):
        trans_tipo = transacciones.filter(tipo_operacion=tipo)
        
        if trans_tipo.exists():
            # Calcular comisión real iterando
            comisiones_pyg = Decimal('0.00')
            descuentos_pyg = Decimal('0.00')
            
            for trans in trans_tipo:
                comisiones_pyg += calcular_comision_real_cambio(trans)
                descuentos_pyg += trans.monto_descuento
            
            ganancia_neta_pyg = comisiones_pyg - descuentos_pyg
            
            ganancias_por_tipo[tipo.codigo] = {
                'tipo': tipo,
                'comisiones_pyg': comisiones_pyg,
                'descuentos_pyg': descuentos_pyg,
                'ganancia_neta_pyg': ganancia_neta_pyg,
                'cantidad': trans_tipo.count(),
            }
    
    return ganancias_por_tipo


@login_required
@permission_required('transacciones.view_reporte_transacciones', raise_exception=True)
def reporte_transacciones(request):
    """
    Vista principal del reporte de transacciones con filtros.
    """
    form = FiltroReporteForm(request.GET or None)
    transacciones = Transaccion.objects.all().select_related(
        'tipo_operacion', 'estado', 'moneda_origen', 'moneda_destino',
        'cliente', 'usuario', 'tauser'
    )
    
    fecha_desde = None
    fecha_hasta = None
    
    if form.is_valid():
        transacciones, fecha_desde, fecha_hasta = aplicar_filtros_transacciones(
            transacciones, 
            form.cleaned_data
        )
    
    # Si no hay fechas especificadas, usar últimos 30 días para los gráficos
    if not fecha_desde:
        fecha_desde = timezone.now().date() - timedelta(days=30)
    if not fecha_hasta:
        fecha_hasta = timezone.now().date()
    
    # Ordenar por fecha descendente
    transacciones = transacciones.order_by('-fecha_creacion')
    
    # Calcular estadísticas
    total_canceladas_anuladas = transacciones.filter(
        estado__codigo__in=['CANCELADA', 'ANULADA']
    ).count()
    
    estadisticas = {
        'total': transacciones.count(),
        'pagadas': transacciones.filter(estado__codigo='PAGADA').count(),
        'pendientes': transacciones.filter(estado__codigo='PENDIENTE').count(),
        'canceladas': total_canceladas_anuladas,
        'compras': transacciones.filter(tipo_operacion__codigo='COMPRA').count(),
        'ventas': transacciones.filter(tipo_operacion__codigo='VENTA').count(),
    }
    
    # Preparar datos para el gráfico de líneas (transacciones por día)
    import json
    transacciones_por_dia = transacciones.annotate(
        fecha=TruncDate('fecha_creacion')
    ).values('fecha').annotate(
        cantidad=Count('id')
    ).order_by('fecha')
    
    # Generar todas las fechas del rango
    fechas_grafico = []
    cantidades_grafico = []
    fecha_actual = fecha_desde
    while fecha_actual <= fecha_hasta:
        fechas_grafico.append(fecha_actual.strftime('%Y-%m-%d'))
        # Buscar si hay transacciones en esa fecha
        cantidad = 0
        for item in transacciones_por_dia:
            if item['fecha'] == fecha_actual:
                cantidad = item['cantidad']
                break
        cantidades_grafico.append(cantidad)
        fecha_actual += timedelta(days=1)
    
    datos_grafico = json.dumps({
        'fechas': fechas_grafico,
        'cantidades': cantidades_grafico
    })
    
    # Implementar paginación
    paginator = Paginator(transacciones, 20)  # 20 transacciones por página
    page = request.GET.get('page', 1)
    
    try:
        transacciones_paginadas = paginator.page(page)
    except PageNotAnInteger:
        transacciones_paginadas = paginator.page(1)
    except EmptyPage:
        transacciones_paginadas = paginator.page(paginator.num_pages)
    
    # Calcular ganancia en PYG para cada transacción
    for transaccion in transacciones_paginadas:
        # CALCULAR COMISIÓN REAL DE CAMBIO (no el costo operativo de métodos)
        transaccion.comision_pyg = calcular_comision_real_cambio(transaccion)
        
        # El descuento siempre está en PYG
        transaccion.descuento_pyg = transaccion.monto_descuento
        
        # Solo calcular ganancia para transacciones completadas
        if transaccion.estado.codigo in ['PAGADA', 'ENTREGADA', 'RETIRADO']:
            transaccion.ganancia_pyg = transaccion.comision_pyg - transaccion.descuento_pyg
        else:
            # Transacciones canceladas/anuladas/pendientes no tienen ganancia
            transaccion.ganancia_pyg = Decimal('0.00')
    
    context = {
        'form': form,
        'transacciones': transacciones_paginadas,
        'estadisticas': estadisticas,
        'datos_grafico': datos_grafico,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_registros': transacciones.count(),
        'page_obj': transacciones_paginadas,
        'is_paginated': paginator.num_pages > 1,
    }
    
    return render(request, 'transacciones/reporte_transacciones.html', context)


@login_required
@permission_required('transacciones.view_reporte_ganancias', raise_exception=True)
def reporte_ganancias(request):
    """
    Vista principal del tablero de control de ganancias con filtros.
    """
    form = FiltroReporteForm(request.GET or None)
    
    # Solo transacciones pagadas generan ganancias
    transacciones = Transaccion.objects.filter(
        estado__codigo__in=['PAGADA', 'ENTREGADA', 'RETIRADO']
    ).select_related(
        'tipo_operacion', 'estado', 'moneda_origen', 'moneda_destino'
    )
    
    fecha_desde = None
    fecha_hasta = None
    
    if form.is_valid():
        transacciones, fecha_desde, fecha_hasta = aplicar_filtros_transacciones(
            transacciones, 
            form.cleaned_data
        )
    
    # Calcular ganancias por moneda
    ganancias_por_moneda = {}
    
    # Calcular totales UNA SOLA VEZ sobre todas las transacciones
    # (no por moneda para evitar contar transacciones dos veces)
    # Necesitamos iterar para calcular comisión real
    total_comisiones_pyg = Decimal('0.00')
    total_descuentos_pyg = Decimal('0.00')
    
    for trans in transacciones:
        total_comisiones_pyg += calcular_comision_real_cambio(trans)
        total_descuentos_pyg += trans.monto_descuento
    
    total_ganancia_pyg = total_comisiones_pyg - total_descuentos_pyg
    
    # Obtener configuración del sistema
    try:
        config = ConfiguracionSistema.obtener_configuracion()
        moneda_base = config.moneda_base
    except:
        moneda_base = Moneda.objects.filter(codigo='PYG').first()
    
    # Solo iterar sobre monedas con tasas de cambio activas
    monedas_con_tasa = Moneda.objects.filter(
        es_activa=True,
        tasas_cambio__es_activa=True
    ).exclude(codigo='PYG').distinct()
    
    for moneda in monedas_con_tasa:
        # Para cada moneda extranjera, buscar transacciones donde es la divisa operada
        # (no PYG, que siempre está presente)
        transacciones_moneda = transacciones.filter(
            Q(moneda_origen=moneda) | Q(moneda_destino=moneda)
        )
        
        if transacciones_moneda.count() == 0:
            continue
        
        # Calcular comisión real iterando (no podemos usar aggregate aquí)
        comision_pyg = Decimal('0.00')
        descuento_pyg = Decimal('0.00')
        
        for trans in transacciones_moneda:
            comision_pyg += calcular_comision_real_cambio(trans)
            descuento_pyg += trans.monto_descuento
        
        ganancia_pyg = comision_pyg - descuento_pyg
        
        # Siempre mostrar si hay transacciones (incluso si comisión es 0)
        ganancias_por_moneda[moneda.codigo] = {
            'moneda': moneda,
            'total_comision': None,  # No aplica porque mezclamos origen/destino
            'total_descuento': None,  # No aplica porque mezclamos origen/destino
            'ganancia_neta': None,   # No aplica porque mezclamos origen/destino
            'comision_pyg': comision_pyg,
            'descuento_pyg': descuento_pyg,
            'ganancia_pyg': ganancia_pyg,
            'cantidad_transacciones': transacciones_moneda.count(),
        }
        # NO sumamos a los totales aquí porque ya se calcularon arriba
        # (cada transacción aparece en múltiples monedas, causaría duplicación)
    
    # Estadísticas generales
    estadisticas = {
        'total_transacciones': transacciones.count(),
        'total_comisiones_pyg': total_comisiones_pyg,
        'total_descuentos_pyg': total_descuentos_pyg,
    }
    
    # Desglose por tipo de operación (convertido a PYG)
    ganancias_por_tipo = calcular_ganancias_por_tipo(transacciones)
    
    context = {
        'form': form,
        'ganancias_por_moneda': ganancias_por_moneda,
        'ganancias_por_tipo': ganancias_por_tipo,
        'estadisticas': estadisticas,
        'total_ganancia_pyg': total_ganancia_pyg,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'moneda_base': moneda_base,
    }
    
    return render(request, 'transacciones/reporte_ganancias.html', context)


@login_required
@permission_required('transacciones.view_reporte_transacciones', raise_exception=True)
def exportar_transacciones_excel(request):
    """
    Exporta el reporte de transacciones a Excel.
    """
    form = FiltroReporteForm(request.GET or None)
    transacciones = Transaccion.objects.all().select_related(
        'tipo_operacion', 'estado', 'moneda_origen', 'moneda_destino',
        'cliente', 'usuario'
    )
    
    if form.is_valid():
        transacciones, fecha_desde, fecha_hasta = aplicar_filtros_transacciones(
            transacciones, 
            form.cleaned_data
        )
    
    transacciones = transacciones.order_by('-fecha_creacion')
    
    # Crear libro de Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Transacciones"
    
    # Estilos
    header_fill = PatternFill(start_color="0d6efd", end_color="0d6efd", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Encabezados
    headers = [
        'ID Transacción', 'Fecha', 'Usuario', 'Cliente', 'Tipo', 'Estado',
        'Moneda Origen', 'Monto Origen', 'Moneda Destino', 'Monto Destino',
        'Tasa Cambio', 'Requiere Retiro', 'TAUSER', 'Comisión (PYG)', 'Descuento (PYG)', 'Ganancia (PYG)'
    ]
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
    
    # Datos
    for row_num, trans in enumerate(transacciones, 2):
        # Calcular comisión real de cambio
        comision_pyg = calcular_comision_real_cambio(trans)
        descuento_pyg = trans.monto_descuento
        
        # Calcular ganancia en PYG solo para transacciones completadas
        if trans.estado.codigo in ['PAGADA', 'ENTREGADA', 'RETIRADO']:
            ganancia_pyg = comision_pyg - descuento_pyg
        else:
            ganancia_pyg = Decimal('0.00')
        
        ws.cell(row=row_num, column=1).value = trans.id_transaccion
        ws.cell(row=row_num, column=2).value = trans.fecha_creacion.strftime('%Y-%m-%d %H:%M')
        ws.cell(row=row_num, column=3).value = f"{trans.usuario.nombre} {trans.usuario.apellido}".strip() if trans.usuario else '-'
        ws.cell(row=row_num, column=4).value = trans.cliente.nombre_comercial if trans.cliente else 'Cliente Casual'
        ws.cell(row=row_num, column=5).value = trans.tipo_operacion.nombre
        ws.cell(row=row_num, column=6).value = trans.estado.nombre
        ws.cell(row=row_num, column=7).value = trans.moneda_origen.codigo
        ws.cell(row=row_num, column=8).value = float(trans.monto_origen)
        ws.cell(row=row_num, column=9).value = trans.moneda_destino.codigo
        ws.cell(row=row_num, column=10).value = float(trans.monto_destino)
        ws.cell(row=row_num, column=11).value = float(trans.tasa_cambio)
        ws.cell(row=row_num, column=12).value = 'Sí' if trans.requiere_retiro_fisico else 'No'
        ws.cell(row=row_num, column=13).value = trans.tauser.nombre if trans.tauser else '-'
        ws.cell(row=row_num, column=14).value = float(comision_pyg)
        ws.cell(row=row_num, column=15).value = float(descuento_pyg)
        ws.cell(row=row_num, column=16).value = float(ganancia_pyg)
        
        # Aplicar bordes
        for col_num in range(1, 17):
            ws.cell(row=row_num, column=col_num).border = border
    
    # Ajustar ancho de columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    # Preparar respuesta
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_transacciones_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


@login_required
@permission_required('transacciones.view_reporte_transacciones', raise_exception=True)
def exportar_transacciones_pdf(request):
    """
    Exporta el reporte de transacciones a PDF.
    """
    form = FiltroReporteForm(request.GET or None)
    transacciones = Transaccion.objects.all().select_related(
        'tipo_operacion', 'estado', 'moneda_origen', 'moneda_destino',
        'cliente', 'usuario'
    )
    
    fecha_desde = None
    fecha_hasta = None
    
    if form.is_valid():
        transacciones, fecha_desde, fecha_hasta = aplicar_filtros_transacciones(
            transacciones, 
            form.cleaned_data
        )
    
    transacciones = transacciones.order_by('-fecha_creacion')
    
    # Calcular estadísticas para el PDF
    total_canceladas_anuladas = transacciones.filter(
        estado__codigo__in=['CANCELADA', 'ANULADA']
    ).count()
    
    estadisticas = {
        'total': transacciones.count(),
        'pagadas': transacciones.filter(estado__codigo='PAGADA').count(),
        'pendientes': transacciones.filter(estado__codigo='PENDIENTE').count(),
        'canceladas': total_canceladas_anuladas,
        'compras': transacciones.filter(tipo_operacion__codigo='COMPRA').count(),
        'ventas': transacciones.filter(tipo_operacion__codigo='VENTA').count(),
    }
    
    # Crear PDF en orientación horizontal para que quepa el UUID completo
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    elements.append(Paragraph("Reporte de Transacciones", title_style))
    elements.append(Spacer(1, 12))
    
    # Período
    if fecha_desde and fecha_hasta:
        periodo_text = f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(periodo_text, styles['Normal']))
        elements.append(Spacer(1, 12))
    
    # Estadísticas
    stats_text = (
        f"<b>Total de transacciones:</b> {estadisticas['total']} | "
        f"<b>Pagadas:</b> {estadisticas['pagadas']} | "
        f"<b>Pendientes:</b> {estadisticas['pendientes']} | "
        f"<b>Canceladas:</b> {estadisticas['canceladas']}"
    )
    stats_para = Paragraph(stats_text, styles['Normal'])
    elements.append(stats_para)
    elements.append(Spacer(1, 20))
    
    # Datos de la tabla
    data = [['ID', 'Fecha', 'Usuario', 'Cliente', 'Tipo', 'Estado', 'Monto origen', 'Monto destino', 'Comisión (PYG)', 'Descuento (PYG)', 'Ganancia (PYG)']]
    
    for trans in transacciones[:100]:  # Limitar a 100 registros en PDF
        usuario_nombre = f"{trans.usuario.nombre} {trans.usuario.apellido}".strip() if trans.usuario else '-'
        cliente_nombre = trans.cliente.nombre_comercial if trans.cliente else 'Casual'
        
        # Formatear montos usando el filtro moneda_format
        monto_origen_fmt = moneda_format(trans.monto_origen, trans.moneda_origen.codigo)
        monto_destino_fmt = moneda_format(trans.monto_destino, trans.moneda_destino.codigo)
        
        # TANTO LA COMISIÓN COMO EL DESCUENTO SIEMPRE ESTÁN EN PYG
        # Calcular comisión real de cambio
        comision_pyg = calcular_comision_real_cambio(trans)
        descuento_pyg = trans.monto_descuento
        
        comision_pyg_fmt = moneda_format(comision_pyg, 'PYG')
        descuento_pyg_fmt = moneda_format(descuento_pyg, 'PYG')
        
        # Calcular ganancia en PYG solo para transacciones completadas
        if trans.estado.codigo in ['PAGADA', 'ENTREGADA', 'RETIRADO']:
            ganancia_pyg = comision_pyg - descuento_pyg
        else:
            ganancia_pyg = Decimal('0.00')
        ganancia_pyg_fmt = moneda_format(ganancia_pyg, 'PYG')
        
        data.append([
            trans.id_transaccion,  # ID completo sin cortar
            trans.fecha_creacion.strftime('%d/%m/%Y'),
            usuario_nombre[:15],
            cliente_nombre[:15],
            trans.tipo_operacion.codigo,
            trans.estado.codigo,
            monto_origen_fmt,
            monto_destino_fmt,
            comision_pyg_fmt,
            descuento_pyg_fmt,
            ganancia_pyg_fmt
        ])
    
    # Crear tabla con anchos de columna específicos
    # Ancho total de página A4 horizontal: aproximadamente 800 puntos disponibles
    col_widths = [
        100,  # ID (UUID - más reducido)
        55,   # Fecha
        70,   # Usuario
        70,   # Cliente
        45,   # Tipo
        50,   # Estado
        75,   # Origen
        75,   # Destino
        70,   # Comisión (PYG)
        70,   # Descuento (PYG)
        70,   # Ganancia (PYG)
    ]
    
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('WORDWRAP', (0, 0), (-1, -1), True),  # Permitir ajuste de texto
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(table)
    
    # Construir PDF
    doc.build(elements)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_transacciones_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response


@login_required
@permission_required('transacciones.view_reporte_ganancias', raise_exception=True)
def exportar_ganancias_excel(request):
    """
    Exporta el tablero de control de ganancias a Excel.
    """
    form = FiltroReporteForm(request.GET or None)
    transacciones = Transaccion.objects.filter(
        estado__codigo__in=['PAGADA', 'ENTREGADA', 'RETIRADO']
    ).select_related('tipo_operacion', 'moneda_origen', 'moneda_destino')
    
    fecha_desde = None
    fecha_hasta = None
    
    if form.is_valid():
        transacciones, fecha_desde, fecha_hasta = aplicar_filtros_transacciones(
            transacciones, 
            form.cleaned_data
        )
    
    # Calcular estadísticas (igual que en la vista principal)
    total_ganancia_pyg = Decimal('0.00')
    total_comisiones_pyg = Decimal('0.00')
    total_descuentos_pyg = Decimal('0.00')
    
    # Calcular por tipo de operación (reutilizando función auxiliar)
    ganancias_por_tipo = calcular_ganancias_por_tipo(transacciones)
    
    # Crear libro de Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte Ganancias"
    
    # Estilos
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    total_fill = PatternFill(start_color="FFD700", end_color="FFD700", fill_type="solid")
    total_font = Font(bold=True)
    
    # Título
    ws.merge_cells('A1:E1')
    title_cell = ws['A1']
    title_cell.value = "TABLERO DE CONTROL DE GANANCIAS"
    title_cell.font = Font(size=14, bold=True, color="366092")
    title_cell.alignment = Alignment(horizontal='center')
    
    # Período si existe
    current_row = 2
    if fecha_desde and fecha_hasta:
        ws.merge_cells(f'A{current_row}:E{current_row}')
        periodo_cell = ws.cell(row=current_row, column=1)
        periodo_cell.value = f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}"
        periodo_cell.alignment = Alignment(horizontal='center')
        current_row += 1
    
    current_row += 1
    
    # Encabezados por moneda
    ws.cell(row=current_row, column=1).value = "Moneda"
    ws.cell(row=current_row, column=2).value = "Total Comisiones"
    ws.cell(row=current_row, column=3).value = "Total Descuentos"
    ws.cell(row=current_row, column=4).value = "Ganancia Neta"
    ws.cell(row=current_row, column=5).value = "Ganancia en PYG"
    
    for col_num in range(1, 6):
        cell = ws.cell(row=current_row, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Calcular ganancias por moneda (solo divisas extranjeras con tasa de cambio activa)
    row_num = current_row + 1
    
    monedas_con_tasa = Moneda.objects.filter(
        es_activa=True,
        tasas_cambio__es_activa=True
    ).exclude(codigo='PYG').distinct()
    
    for moneda in monedas_con_tasa:
        transacciones_moneda = transacciones.filter(
            Q(moneda_origen=moneda) | Q(moneda_destino=moneda)
        )
        
        if transacciones_moneda.count() == 0:
            continue
        
        # Calcular comisión real iterando
        comision_total = Decimal('0.00')
        descuento_total = Decimal('0.00')
        
        for trans in transacciones_moneda:
            comision_total += calcular_comision_real_cambio(trans)
            descuento_total += trans.monto_descuento
        
        ganancia_neta = comision_total - descuento_total
        
        # Siempre mostrar si hay transacciones (incluso si comisión es 0)
        # Los valores ya están en PYG
        ws.cell(row=row_num, column=1).value = moneda.codigo
        ws.cell(row=row_num, column=2).value = float(comision_total)
        ws.cell(row=row_num, column=3).value = float(descuento_total)
        ws.cell(row=row_num, column=4).value = float(ganancia_neta)
        ws.cell(row=row_num, column=5).value = float(ganancia_neta)  # Ya está en PYG
        
        total_ganancia_pyg += ganancia_neta
        total_comisiones_pyg += comision_total
        total_descuentos_pyg += descuento_total
        row_num += 1
    
    # Fila de total
    ws.cell(row=row_num, column=1).value = "TOTAL (PYG)"
    ws.cell(row=row_num, column=2).value = float(total_comisiones_pyg)
    ws.cell(row=row_num, column=3).value = float(total_descuentos_pyg)
    ws.cell(row=row_num, column=4).value = ""
    ws.cell(row=row_num, column=5).value = float(total_ganancia_pyg)
    
    for col_num in range(1, 6):
        cell = ws.cell(row=row_num, column=col_num)
        cell.fill = total_fill
        cell.font = total_font
        cell.alignment = Alignment(horizontal='center')
    
    row_num += 2
    
    # Estadísticas generales
    ws.merge_cells(f'A{row_num}:E{row_num}')
    stats_cell = ws.cell(row=row_num, column=1)
    stats_cell.value = "ESTADÍSTICAS GENERALES"
    stats_cell.font = Font(size=12, bold=True)
    stats_cell.alignment = Alignment(horizontal='center')
    row_num += 1
    
    stats_data = [
        ['Total Transacciones', transacciones.count()],
        ['Total Comisiones (PYG)', float(total_comisiones_pyg)],
        ['Total Descuentos (PYG)', float(total_descuentos_pyg)],
        ['Ganancia Total (PYG)', float(total_ganancia_pyg)],
    ]
    
    for stat in stats_data:
        ws.cell(row=row_num, column=1).value = stat[0]
        ws.cell(row=row_num, column=1).font = Font(bold=True)
        ws.cell(row=row_num, column=2).value = stat[1]
        row_num += 1
    
    # Ganancias por tipo de operación
    if ganancias_por_tipo:
        row_num += 1
        ws.merge_cells(f'A{row_num}:E{row_num}')
        tipo_cell = ws.cell(row=row_num, column=1)
        tipo_cell.value = "GANANCIAS POR TIPO DE OPERACIÓN"
        tipo_cell.font = Font(size=12, bold=True)
        tipo_cell.alignment = Alignment(horizontal='center')
        row_num += 1
        
        # Encabezados para tipos de operación
        headers_tipo = ['Tipo de Operación', 'Comisiones (PYG)', 'Descuentos (PYG)', 'Ganancia Neta (PYG)', 'Transacciones']
        for col_num, header in enumerate(headers_tipo, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        row_num += 1
        
        for codigo, data in ganancias_por_tipo.items():
            ws.cell(row=row_num, column=1).value = data['tipo'].nombre
            ws.cell(row=row_num, column=1).font = Font(bold=True)
            ws.cell(row=row_num, column=2).value = float(data['comisiones_pyg'])
            ws.cell(row=row_num, column=3).value = float(data['descuentos_pyg'])
            ws.cell(row=row_num, column=4).value = float(data['ganancia_neta_pyg'])
            ws.cell(row=row_num, column=5).value = data['cantidad']
            row_num += 1
    
    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 20
    
    # Preparar respuesta
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_ganancias_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    return response


@login_required
@permission_required('transacciones.view_reporte_ganancias', raise_exception=True)
def exportar_ganancias_pdf(request):
    """
    Exporta el tablero de control de ganancias a PDF.
    """
    form = FiltroReporteForm(request.GET or None)
    transacciones = Transaccion.objects.filter(
        estado__codigo__in=['PAGADA', 'ENTREGADA', 'RETIRADO']
    ).select_related('tipo_operacion', 'moneda_origen', 'moneda_destino')
    
    fecha_desde = None
    fecha_hasta = None
    
    if form.is_valid():
        transacciones, fecha_desde, fecha_hasta = aplicar_filtros_transacciones(
            transacciones, 
            form.cleaned_data
        )
    
    # Calcular estadísticas (igual que en la vista)
    total_ganancia_pyg = Decimal('0.00')
    total_comisiones_pyg = Decimal('0.00')
    total_descuentos_pyg = Decimal('0.00')
    
    # Calcular por tipo de operación (reutilizando función auxiliar)
    ganancias_por_tipo = calcular_ganancias_por_tipo(transacciones)
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    elements.append(Paragraph("Tablero de Control de Ganancias", title_style))
    elements.append(Spacer(1, 12))
    
    # Período
    if fecha_desde and fecha_hasta:
        periodo_text = f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(periodo_text, styles['Normal']))
        elements.append(Spacer(1, 12))
    
    # Calcular ganancias (solo divisas extranjeras con tasa de cambio activa)
    data = [['Moneda', 'Comisiones', 'Descuentos', 'Ganancia Neta', 'Ganancia PYG']]
    
    monedas_con_tasa = Moneda.objects.filter(
        es_activa=True,
        tasas_cambio__es_activa=True
    ).exclude(codigo='PYG').distinct()
    
    for moneda in monedas_con_tasa:
        transacciones_moneda = transacciones.filter(
            Q(moneda_origen=moneda) | Q(moneda_destino=moneda)
        )
        
        if transacciones_moneda.count() == 0:
            continue
        
        # Calcular comisión real iterando
        comision_total = Decimal('0.00')
        descuento_total = Decimal('0.00')
        
        for trans in transacciones_moneda:
            comision_total += calcular_comision_real_cambio(trans)
            descuento_total += trans.monto_descuento
        
        ganancia_neta = comision_total - descuento_total
        
        # Siempre mostrar si hay transacciones (incluso si comisión es 0)
        # Los valores ya están en PYG
        data.append([
            moneda.codigo,
            f"{comision_total:,.2f}",
            f"{descuento_total:,.2f}",
            f"{ganancia_neta:,.2f}",
            f"{ganancia_neta:,.2f}"  # Ya está en PYG
        ])
        
        total_ganancia_pyg += ganancia_neta
        total_comisiones_pyg += comision_total
        total_descuentos_pyg += descuento_total
    
    # Fila de total
    data.append([
        'TOTAL (PYG)',
        f"{total_comisiones_pyg:,.0f}",
        f"{total_descuentos_pyg:,.0f}",
        '',
        f"{total_ganancia_pyg:,.2f}"
    ])
    
    # Crear tabla de ganancias por moneda
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFD700')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 30))
    
    # Estadísticas generales
    elements.append(Paragraph("Estadísticas Generales", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    stats_data = [
        ['Métrica', 'Valor'],
        ['Total Transacciones', str(transacciones.count())],
        ['Total Comisiones (PYG)', f"{total_comisiones_pyg:,.0f}"],
        ['Total Descuentos (PYG)', f"{total_descuentos_pyg:,.0f}"],
        ['Ganancia Total (PYG)', f"{total_ganancia_pyg:,.0f}"]
    ]
    
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(stats_table)
    
    # Ganancias por tipo de operación
    if ganancias_por_tipo:
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Ganancias por Tipo de Operación", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        tipo_data = [['Tipo de Operación', 'Comisiones (PYG)', 'Descuentos (PYG)', 'Ganancia Neta (PYG)', 'Transacciones']]
        for codigo, data_tipo in ganancias_por_tipo.items():
            tipo_data.append([
                data_tipo['tipo'].nombre,
                f"{data_tipo['comisiones_pyg']:,.0f}",
                f"{data_tipo['descuentos_pyg']:,.0f}",
                f"{data_tipo['ganancia_neta_pyg']:,.0f}",
                str(data_tipo['cantidad'])
            ])
        
        tipo_table = Table(tipo_data)
        tipo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(tipo_table)
    
    # Construir PDF
    doc.build(elements)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_ganancias_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    
    return response

----
Perfecto! Ahora vamos a crear los templates. Primero veamos la estructura del directorio de templates:

<div class="container mt-4">
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-exchange-alt me-1"></i>Mis transacciones
            </li>
        </ol>
    </nav>

    <div class="d-flex justify-content-start mb-3">
        <a href="{% url 'auth:dashboard' %}" class="btn btn-outline-secondary">
            <i class="fas fa-arrow-left me-2"></i>Volver al Dashboard
        </a>
    </div>

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h2">
            <i class="fas fa-exchange-alt text-primary me-2"></i>
            Mis transacciones
        </h1>
    </div>

    <!-- Estadísticas rápidas -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5 class="card-title">Total</h5>
                            <h2>{{ estadisticas.total_transacciones }}</h2>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-list fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5 class="card-title">Pagadas</h5>
                            <h2>{{ estadisticas.pagadas }}</h2>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-check-circle fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5 class="card-title">Pendientes</h5>
                            <h2>{{ estadisticas.pendientes }}</h2>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-clock fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-danger text-white">
                <div class="card-body">
                    <div class="d-flex justify-content-between">
                        <div>
                            <h5 class="card-title">Canceladas</h5>
                            <h2>{{ estadisticas.canceladas|add:estadisticas.anuladas }}</h2>
                        </div>
                        <div class="align-self-center">
                            <i class="fas fa-times-circle fa-2x opacity-75"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Gráfico opcional -->
    {% if estadisticas.total_transacciones > 0 %}
    <div class="row mb-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-chart-line me-2"></i>
                        {% if filtros.fecha_desde or filtros.fecha_hasta %}
                            Transacciones en el período seleccionado
                        {% else %}
                            Transacciones de los últimos 30 días
                        {% endif %}
                    </h5>
                </div>
                <div class="card-body">
                    <canvas id="transaccionesChart" height="200"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>Por Tipo de Operación</h5>
                </div>
                <div class="card-body">
                    <canvas id="tiposChart" height="200"></canvas>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Filtros -->
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-3">
                    <label for="fecha_desde" class="form-label">Fecha Desde</label>
                    <input type="date" id="fecha_desde" name="fecha_desde" class="form-control" value="{{ filtros.fecha_desde }}" />
                </div>
                <div class="col-md-3">
                    <label for="fecha_hasta" class="form-label">Fecha Hasta</label>
                    <input type="date" id="fecha_hasta" name="fecha_hasta" class="form-control" value="{{ filtros.fecha_hasta }}" />
                </div>
                <div class="col-md-2">
                    <label for="tipo" class="form-label">Tipo</label>
                    <select id="tipo" name="tipo" class="form-select">
                        <option value="">Todos</option>
                        {% for tipo in tipos_operacion %}
                        <option value="{{ tipo.pk }}" {% if filtros.tipo == tipo.pk|stringformat:"s" %}selected{% endif %}>
                            {% if tipo.codigo == 'VENTA' %}
                            Compra de Divisas
                            {% else %}
                            Venta de Divisas
                            {% endif %}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="estado" class="form-label">Estado</label>
                    <select id="estado" name="estado" class="form-select">
                        <option value="">Todos</option>
                        {% for estado in estados_transaccion %}
                        <option value="{{ estado.pk }}" {% if filtros.estado == estado.pk|stringformat:"s" %}selected{% endif %}>
                            {{ estado.nombre }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2">
                    <label for="cliente" class="form-label">Cliente</label>
                    <select id="cliente" name="cliente" class="form-select">
                        <option value="">Todos</option>
                        {% for cliente in clientes %}
                        <option value="{{ cliente.pk }}" {% if filtros.cliente == cliente.pk|stringformat:"s" %}selected{% endif %}>
                            {{ cliente.nombre_comercial }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-12 d-flex justify-content-end">
                    <button type="submit" class="btn btn-primary me-2">
                        <i class="fas fa-search me-1"></i>Filtrar
                    </button>
                    <a href="{% url 'transacciones:mis_transacciones' %}" class="btn btn-outline-secondary">
                        <i class="fas fa-times me-1"></i>Limpiar
                    </a>
                </div>
            </form>
        </div>
    </div>

    <!-- Tabla de transacciones -->
    {% if transacciones %}
    <div class="card shadow-sm">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>ID Transacción</th>
                            <th>Fecha</th>
                            <th>Cliente</th>
                            <th>Tipo</th>
                            <th>Estado</th>
                            <th>Moneda Origen</th>
                            <th>Monto Origen</th>
                            <th>Moneda Destino</th>
                            <th>Monto Destino</th>
                            <th class="text-center">Retiro</th>
                            <th class="text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for transaccion in transacciones %}
                        <tr>
                            <td><strong>{{ transaccion.id_transaccion }}</strong></td>
                            <td><small class="text-muted">{{ transaccion.fecha_creacion|date:"d/m/Y H:i" }}</small></td>
                            <td>
                                {% if transaccion.cliente %}
                                    {{ transaccion.cliente.nombre_comercial }}
                                {% else %}
                                    <em class="text-muted">Casual</em>
                                {% endif %}
                            </td>
                            <td>
                                {% if transaccion.tipo_operacion.codigo == 'VENTA' %}
                                <span class="badge bg-info">Compra de Divisas</span>
                                {% else %}
                                <span class="badge bg-info">Venta de Divisas</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if transaccion.estado.codigo == 'PAGADA' %}
                                <span class="badge bg-success">
                                    <i class="fas fa-check me-1"></i>{{ transaccion.estado.nombre }}
                                </span>
                                {% elif transaccion.estado.codigo == 'PENDIENTE' %}
                                <span class="badge bg-warning">
                                    <i class="fas fa-clock me-1"></i>{{ transaccion.estado.nombre }}
                                </span>
                                {% elif transaccion.estado.codigo == 'CANCELADA' %}
                                <span class="badge bg-danger">
                                    <i class="fas fa-times me-1"></i>{{ transaccion.estado.nombre }}
                                </span>
                                {% elif transaccion.estado.codigo == 'ANULADA' %}
                                <span class="badge bg-secondary">
                                    <i class="fas fa-ban me-1"></i>{{ transaccion.estado.nombre }}
                                </span>
                                {% else %}
                                <span class="badge bg-secondary">{{ transaccion.estado.nombre }}</span>
                                {% endif %}
                            </td>
                            <td>{{ transaccion.moneda_origen.codigo }}</td>
                            <td class="text-end">
                                {% if transaccion.moneda_origen.codigo == 'PYG' %}
                                    ₲ {{ transaccion.monto_origen|floatformat:0|floatformat:"g" }}
                                {% else %}
                                    {{ transaccion.moneda_origen.simbolo }} {{ transaccion.monto_origen|floatformat:2 }}
                                {% endif %}
                            </td>
                            <td>{{ transaccion.moneda_destino.codigo }}</td>
                            <td class="text-end">
                                {% if transaccion.moneda_destino.codigo == 'PYG' %}
                                    ₲ {{ transaccion.monto_destino|floatformat:0|floatformat:"g" }}
                                {% else %}
                                    {{ transaccion.moneda_destino.simbolo }} {{ transaccion.monto_destino|floatformat:2 }}
                                {% endif %}
                            </td>
                            <td class="text-center">
                                {% if transaccion.requiere_retiro_fisico %}
                                    {% if transaccion.tauser %}
                                        <span class="badge bg-success" title="Retirado en {{ transaccion.tauser.nombre }}">
                                            <i class="fas fa-check me-1"></i>Retirado
                                        </span>
                                        <br>
                                        <small class="text-muted">{{ transaccion.tauser.nombre }}</small>
                                    {% else %}
                                        <span class="badge bg-warning" title="Pendiente de retiro">
                                            <i class="fas fa-clock me-1"></i>Pendiente
                                        </span>
                                    {% endif %}
                                {% else %}
                                    <span class="badge bg-secondary" title="No requiere retiro físico">
                                        <i class="fas fa-times me-1"></i>No aplica
                                    </span>
                                {% endif %}
                            </td>
                            <td class="text-center">
                                <div class="btn-group" role="group">
                                    <a href="{% url 'transacciones:resumen_transaccion' transaccion.id_transaccion %}"
                                       class="btn btn-sm btn-outline-primary" title="Ver resumen">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% if is_paginated %}
            <nav aria-label="Navegación de páginas" class="mt-3">
                <ul class="pagination justify-content-center">
                    {% if page_obj.has_previous %}
                    <li class="page-item"><a class="page-link" href="?page=1{% if request.GET.fecha_desde %}&fecha_desde={{ request.GET.fecha_desde }}{% endif %}{% if request.GET.fecha_hasta %}&fecha_hasta={{ request.GET.fecha_hasta }}{% endif %}{% if request.GET.tipo %}&tipo={{ request.GET.tipo }}{% endif %}{% if request.GET.estado %}&estado={{ request.GET.estado }}{% endif %}{% if request.GET.cliente %}&cliente={{ request.GET.cliente }}{% endif %}"><i class="fas fa-angle-double-left"></i></a></li>
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.fecha_desde %}&fecha_desde={{ request.GET.fecha_desde }}{% endif %}{% if request.GET.fecha_hasta %}&fecha_hasta={{ request.GET.fecha_hasta }}{% endif %}{% if request.GET.tipo %}&tipo={{ request.GET.tipo }}{% endif %}{% if request.GET.estado %}&estado={{ request.GET.estado }}{% endif %}{% if request.GET.cliente %}&cliente={{ request.GET.cliente }}{% endif %}"><i class="fas fa-angle-left"></i></a></li>
                    {% endif %}
                    <li class="page-item active"><span class="page-link">Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}</span></li>
                    {% if page_obj.has_next %}
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.fecha_desde %}&fecha_desde={{ request.GET.fecha_desde }}{% endif %}{% if request.GET.fecha_hasta %}&fecha_hasta={{ request.GET.fecha_hasta }}{% endif %}{% if request.GET.tipo %}&tipo={{ request.GET.tipo }}{% endif %}{% if request.GET.estado %}&estado={{ request.GET.estado }}{% endif %}{% if request.GET.cliente %}&cliente={{ request.GET.cliente }}{% endif %}"><i class="fas fa-angle-right"></i></a></li>
                    <li class="page-item"><a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if request.GET.fecha_desde %}&fecha_desde={{ request.GET.fecha_desde }}{% endif %}{% if request.GET.fecha_hasta %}&fecha_hasta={{ request.GET.fecha_hasta }}{% endif %}{% if request.GET.tipo %}&tipo={{ request.GET.tipo }}{% endif %}{% if request.GET.estado %}&estado={{ request.GET.estado }}{% endif %}{% if request.GET.cliente %}&cliente={{ request.GET.cliente }}{% endif %}"><i class="fas fa-angle-double-right"></i></a></li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
        </div>
    </div>
    {% else %}
    <div class="alert alert-info">
        <i class="fas fa-info-circle me-2"></i>
        No se encontraron transacciones que coincidan con los filtros seleccionados.
    </div>
    {% endif %}
</div>

{% if estadisticas.total_transacciones > 0 %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Gráfico de líneas - Transacciones por día
    const ctx = document.getElementById('transaccionesChart');
    if (ctx) {
        const datosGrafico = JSON.parse('{{ datos_grafico|escapejs }}');

        // Verificar si hay datos para mostrar
        const totalTransacciones = datosGrafico.cantidades.reduce((a, b) => a + b, 0);

        if (totalTransacciones === 0) {
            // Mostrar mensaje si no hay datos
            ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
            const ctxContext = ctx.getContext('2d');
            ctxContext.font = '16px Arial';
            ctxContext.fillStyle = '#6c757d';
            ctxContext.textAlign = 'center';
            ctxContext.fillText('No hay transacciones en el período seleccionado', ctx.width / 2, ctx.height / 2);
        } else {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: datosGrafico.fechas.map(fecha => {
                        const d = new Date(fecha + 'T00:00:00');
                        return d.toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit' });
                    }),
                    datasets: [{
                        label: 'Transacciones por día',
                        data: datosGrafico.cantidades,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.2,
                        pointBackgroundColor: 'rgb(54, 162, 235)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    const fecha = datosGrafico.fechas[context[0].dataIndex];
                                    const d = new Date(fecha + 'T00:00:00');
                                    return d.toLocaleDateString('es-PY', {
                                        weekday: 'long',
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric'
                                    });
                                },
                                label: function(context) {
                                    const cantidad = context.parsed.y;
                                    return cantidad === 1 ? '1 transacción' : `${cantidad} transacciones`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Fecha'
                            },
                            ticks: {
                                maxTicksLimit: 10
                            }
                        },
                        y: {
                            beginAtZero: true,
                            display: true,
                            title: {
                                display: true,
                                text: 'Cantidad de Transacciones'
                            },
                            ticks: {
                                stepSize: 1,
                                callback: function(value) {
                                    if (Number.isInteger(value)) {
                                        return value;
                                    }
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // Gráfico de dona - Tipos de operación
    const ctxTipos = document.getElementById('tiposChart');
    if (ctxTipos) {
        const compras = {{ estadisticas_tipo.compras }};
        const ventas = {{ estadisticas_tipo.ventas }};

        new Chart(ctxTipos, {
            type: 'doughnut',
            data: {
                labels: ['Compras', 'Ventas'],
                datasets: [{
                    data: [compras, ventas],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',
                        'rgba(255, 193, 7, 0.8)'
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(255, 193, 7, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
});
</script>
{% endif %}
{% endblock %}