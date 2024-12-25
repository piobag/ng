window.addEventListener('load', (event) => {
    // reload_ferias()
})

function reload_ferias(filter='conflict') {
    if (filter == 'conflict') {
        reload_datatable('#ferias_up', '/ferias/conflict')
        document.getElementById('ferias_title').innerHTML = 'Conflitantes'
    } else if (filter == 'confirmed') {
        reload_datatable('#ferias_up', '/ferias/confirmed')
        document.getElementById('ferias_title').innerHTML = 'Confirmados'
    } else if (filter == 'rejected') {
        reload_datatable('#ferias_up', '/ferias/rejected')
        document.getElementById('ferias_title').innerHTML = 'Rejeitados'
    }
    reload_datatable('#ferias_down', '/ferias/pending')
}

function reload_datatable(dtable, url) {
    if ( $.fn.dataTable.isDataTable(dtable) ) {
        table = $(dtable).DataTable()
        table.ajax.url(url).search('').draw()
    } else {
        $(dtable).DataTable({
            ajax: url,
            serverSide: true,
            language: {
                url: '/static/datatable.json'
            },
            columns: [
                {
                    data: 'id',
                    visible: false,
                    searchable: false
                },
                {data: 'user', orderable: false},
                {data: 'start', searchable: false},
                {data: 'end', searchable: false},
                {data: 'days', searchable: false, orderable: false},
                {data: 'confirmed', searchable: false, orderable: false},
                {data: 'rejected', searchable: false, orderable: false, visible: false}
            ],
            drawCallback: function( ) {
                var api = this.api()
                api.rows().every( function ( rowIdx, tableLoop, rowLoop ) {
                    var d = this.data()
                    if (d['confirmed']) {
                        this.cell(':eq(' + rowIdx  + ')', -2).data('<i style="color: #198754;" class="far fa-calendar-check"></i>')
                    } else if (d['rejected']) {
                        this.cell(':eq(' + rowIdx  + ')', -2).data('<i style="color: #f00;" class="fas fa-times"></i>')
                    } else {
                        this.cell(':eq(' + rowIdx  + ')', -2).data('<button class="btn btn-sm btn-outline-success" onclick="confirm_ferias(\''+d['id']+'\',\'confirm\')"><i class="fas fa-sm fa-check"></i></button>  <button class="btn btn-sm btn-outline-danger" onclick="confirm_ferias(\''+d['id']+'\',\'reject\')"><i class="fa fa-sm fa-times"></i></button>')
                    }
                } )
            }
        })
    }
}

function confirm_ferias(id, resp) {
    if (resp == 'confirm') {text = 'CONFIRMAR'}
    else if (resp == 'reject') {text = 'REJEITAR'}
    else {
        alert('Parametro inválido')
        return
    }
    if (confirm("Deseja "+text+" o período de férias solicitado?")) {
        $.ajax({
            url: '/ferias/',
            type: 'PUT',
            data: {id: id, resp: resp}}
        ).done(function(data) {
            response = data['result']
            if (response) {alert(response)}
            else {
                alert('Erro chamando a API.')
            }
            reload_ferias('confirmed')
            reload_ferias('pending')
        }).fail(function(data) {
            response = data['responseJSON']
            if (response) {alert(response['error'])}
            else {
                alert('Erro ao confirmar as férias!')
            }
        })
    }
}