window.addEventListener('load', (event) => {
    load_ferias()
    dias_ferias()
})
const new_ferias = document.forms.ferias_new_form
const dias_ferias_elem = $('ferias_dias')

function dias_ferias(){
    if (new_ferias.start.value && new_ferias.end.value) {
        dias_ferias_elem.innerHTML = `${ Math.abs( new Date(new_ferias.start.value) - new Date(new_ferias.end.value)) /(1000 * 3600 * 24) + 1 } {{ _('Days selected') }}`
    }
}

function load_ferias() {
    let update_btn = $('ferias_load_btn')
    let update_html = update_btn.innerHTML
    update_btn.innerHTML = spinner_w

    let api_url = "{{ url_for('ferias.index') }}"
    fetch(api_url)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            $('ferias_list_content').innerHTML = `
                ${result.map(f => `
                    <tr>
                        <td>
                            <span>${new Date(f.start * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</span>
                        </td>
                        <td>
                            <span>${new Date(f.end * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</span>
                        </td>
                        <td>
                            <span class="badge bg-primary rounded-pill mx-2">${ Math.abs(new Date(f.start * 1000) - new Date(f.end * 1000)) /(1000 * 3600 * 24) + 1 }</span>
                        </td>
                        <td>
                            <span>${f.confirmed ? `<b style="color: #198754;"><i class="fas fa-sm fa-check"></i></b>` : f.rejected ? `<b style="color: #dc3545;"><i class="fas fa-sm fa-times"></i></b>` : `<button class="btn btn-sm btn-outline-danger" onclick="delete_ferias(this, '${f.id}')">Cancelar</button>`}</span> 
                        </td>
                `).join('')}`
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) } })
    .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
    .finally(() => update_btn.innerHTML = update_html)
}

function save_ferias(that) {
    if (! new_ferias.checkValidity()) {
        alert('Escolha um intervalo de dias que deseja tirar férias.')
        return
    }
    if (new_ferias.start.value > new_ferias.end.value) {
        alert('O dia final não pode ser antes do dia inicial!')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let api_url = "{{ url_for('ferias.new') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( {
            'start': new_ferias.start.value,
            'end': new_ferias.end.value,
        } ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            load_ferias()
            new_ferias.reset()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        that.innerHTML = btn_html })
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html
    })
}
function delete_ferias(that, fid) {
    if (confirm("Deseja realmente CANCELAR o pedido de férias?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w

        let api_url = "{{ url_for('ferias.delete') }}"
        fetch(api_url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'delete': fid} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                load_ferias()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html
        })
    }
}

{% if 'fin' in roles %}
    window.addEventListener('load', (event) => {
        ferias_list_count = 2
        load_ferias_list('pending')
        load_ferias_list('conflicting')
        load_ferias_list('aproved')
    })

    const ferias_list_pending = $('ferias_list_pending')
    const ferias_list_conflicting = $('ferias_list_conflicting')
    const ferias_list_aproved = $('ferias_list_aproved')
    const ferias_list_update_html = '<i class="fas fa-sm fa-sync"></i>'
    let ferias_list_count = 0
    let ferias_list_filters = {
        'pending': [0,5],
        'conflicting': [0,5],
        'aproved': [0,5],
    }

    function ferias_list_page(page, filter) {
        let filter_values = ferias_list_filters[filter]
        if (! filter_values) {
            alert('Filtro inválido')
            return
        }
        ferias_list_filters[filter][0] = (page*filter_values[1])-filter_values[1]
        load_ferias_list(filter)
    }
    function ferias_list_change_perpage(that, filter) {
        ferias_list_filters[filter][1] = parseInt(that.value)
        load_ferias_list(filter)
    }

    function list_ferias(result){
        let f_values = ferias_list_filters[result['filter']]
        return `
            ${pagination(result['total'], 'ferias_list', f_values[0], f_values[1], result['filter'])}
            <ul class="list-group list-group-flush list-group-item-action">
                ${result['list'].map(f => `
                    <li class="list-group-item list-group-item-action ">
                        <div>
                            <span><b>${f.user}</b></span>
                        </div> 
                        <div>
                            <span>${new Date(f.start * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })} - ${new Date(f.end * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</span>
                            <span class="badge bg-primary rounded-pill mx-2">${ Math.abs(new Date(f.start * 1000) - new Date(f.end * 1000)) /(1000 * 3600 * 24) + 1 }</span>
                            <span>${f.confirmed ? '<i style="color: #198754;" class="far fs-sm fa-calendar-check"></i>' : `
                                        <div class="btn-group btn-group-sm" role="group">
                                            <button class="btn btn-sm btn-outline-success" type="button" onclick="confirm_ferias(this, '${f.id}')"><i class="fas fa-sm fa-check"></i></button>
                                            <button class="btn btn-sm btn-outline-danger" type="button" onclick="reject_ferias(this, '${f.id}')"><i class="fa fa-sm fa-times"></i></button>
                                        </div`}
                            </span> 
                        </div>
                    </li>
                `).join('')}
            </ul>
            Filtrando de ${f_values[0]+1} até ${result['total'] < f_values[0]+f_values[1] ? result['total'] : f_values[0]+f_values[1]} do total de ${result['total']} itens.
        `
    }

    function load_ferias_list(filter) {
        let f_values = ferias_list_filters[filter]
        let update_elem = $('ferias_update_btn')
        update_elem.innerHTML = spinner_w

        let api_url = `{{ url_for('ferias.list') }}?start=${f_values[0]}&length=${f_values[1]}&filter=${filter}`
        fetch(api_url)
        .then(response => response.json()).then(data => {
            result = data['ok']
            if (result) {
                data['filter'] = filter
                let ferias_elem = $(`ferias_list_${filter}`)
                ferias_elem.innerHTML = list_ferias(data)
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
        .finally(() => {
            if (devol_list_count === 0) {
                update_elem.innerHTML = devol_list_update_html
            } else {devol_list_count -= 1}
        })
    }

    function ferias_update() {
        let filters = Object.keys(ferias_list_filters)
        ferias_list_count = filters.length-1
        for (i of filters) {
            load_ferias_list(i)
        }
    }

    function confirm_ferias(that, fid) {
        if (confirm("Deseja CONFIRMAR a solicitação de férias?")) {
            let btn_html = that.innerHTML
            that.innerHTML = spinner_w

            let api_url = "{{ url_for('ferias.edit') }}"
            fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify( {'confirm': fid} ) })
            .then(response => response.json()).then(data => {
                result = data['result']
                if (result) {
                    ferias_update()
                } else {
                    data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                    that.innerHTML = btn_html
                }})
            .catch(error => {
                alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
                that.innerHTML = btn_html
            })
        }
    }
    function reject_ferias(that, fid) {
        if (confirm("Deseja REJEITAR a solicitação de férias?")) {
            let btn_html = that.innerHTML
            that.innerHTML = spinner_w

            let api_url = "{{ url_for('ferias.edit') }}"
            fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify( {'reject': fid} ) })
            .then(response => response.json()).then(data => {
                result = data['result']
                if (result) {
                    ferias_update()
                } else {
                    data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                    that.innerHTML = btn_html
                }})
            .catch(error => {
                alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
                that.innerHTML = btn_html
            })
        }
    }
{% endif %}
