window.addEventListener('load', (event) => {
    devol_list_count = 2
    load_devols('pending')
    load_devols('waiting')
    load_devols('finished')
})

const devol_form_new = document.forms.devol_new
const devol_list_pending = $('devol_list_pending')
const devol_list_waiting = $('devol_list_waiting')
const devol_list_finished = $('devol_list_finished')
const devol_list_update_html = '<i class="fas fa-sm fa-sync"></i>'
let devol_list_count = 0

// Devol List
let devol_list_filters = {
    // table: (start, perpage)
    'waiting': [0,5],
    'finished': [0,5],
    'pending': [0,5],
}

function devol_list_page(page, filter) {
    let filter_values = devol_list_filters[filter]
    if (! filter_values) {
        alert('Filtro inválido')
        return
    }
    devol_list_filters[filter][0] = (page*filter_values[1])-filter_values[1]
    load_devols(filter)
}
function devol_list_change_perpage(that, filter) {
    devol_list_filters[filter][1] = parseInt(that.value)
    load_devols(filter)
}

function list_devol(result) {
    let f_values = devol_list_filters[result['filter']]
    return `
        ${pagination(result['total'], 'devol_list', f_values[0], f_values[1], result['filter'])}
        <table class="table table-sm table-hover table-responsive">
            <thead>
                <tr>
                <th>{{ _('Protocol') }}</th>
                <th>{{ _('Date') }}</th>
                <th>{{ _('Value') }}</th>
                <th></th>
                </tr>
            </thead>
            <tbody>
            ${result['list'].map(d => `
                <tr onclick="open_devol_modal('${d.id}')">
                    <td><b><a><i class="fas fa-sm fa-arrow-alt-circle-right"></i> ${d.prot}</a></b></td>
                    <td>${new Date(d.senddate * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</td>
                    <td>${d.value.toLocaleString('pt-BR', currency_br)}</td>
                    <td>${d.paid ? `<button title="Detalhes" class="btn btn-sm btn-outline-dark"><i class="fa fs-sm fa-check"></i></button>` : d.choice == 'transf' ? `<button title="Confirmar tranferência" class="btn btn-sm btn-outline-success"><i class="fas fa-dollar-sign"></i></button>` : 
                        d.choice == 'retire' ? `<button title="Confirmar cheque" class="btn btn-sm btn-outline-danger"><i class="fas fa-money-check-alt"></i></button>` : `
                        <button title="Reenviar email" class="btn btn-sm btn-outline-warning"><i class="fa fa-sm fa-envelope"></i></button>`}
                    </td>
                </tr>
            `).join('')}
            </tbody>
        </table>
        Filtrando de ${f_values[0]+1} até ${parseInt(result['total']) < f_values[0]+f_values[1] ? result['total'] : f_values[0]+f_values[1]} do total de ${result['total']} itens. 
    `
}


async function load_devols(filter, search='') {
    let f_values = devol_list_filters[filter]
    let update_elem = $('devol_update_btn')
    update_elem.innerHTML = spinner_w
    
    let api_url = `{{ url_for('finance.devols') }}?start=${f_values[0]}&length=${f_values[1]}&filter=${filter}&search=${search}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            data['filter'] = filter
            switch (filter) {
                case 'waiting':
                    if (data['total'] != 0) {
                        devol_list_waiting.innerHTML = `<h5> {{ _('Waiting') }} </h5>`
                        devol_list_waiting.insertAdjacentHTML("beforeend", list_devol(data))
                    } else {
                        devol_list_waiting.innerHTML = ''
                    }
                    break
                case 'finished':
                    if (data['total'] != 0) {
                        devol_list_finished.innerHTML = `<h5> {{ _('Finished') }} </h5>`
                        devol_list_finished.insertAdjacentHTML("beforeend", list_devol(data))
                    } else {
                        devol_list_finished.innerHTML = ''
                    }
                    break
                case 'pending':
                    if (data['total'] != 0) {
                        devol_list_pending.innerHTML = `<h5> {{ _('Pending') }} </h5>`
                        devol_list_pending.insertAdjacentHTML("beforeend", list_devol(data))
                    } else {
                        devol_list_pending.innerHTML = ''
                    }
                    break
                default:
                    break
            }
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) } })
    .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
    .finally(() => {
        if (devol_list_count === 0) {
            update_elem.innerHTML = devol_list_update_html
        } else {devol_list_count -= 1}
    })
}

let devol_update = async function (filter=false) {
    if (filter) {
        load_devols(filter)
    } else {
        let filters = ['pending', 'waiting', 'finished']
        devol_list_count = filters.length-1
        filters.forEach(i => {
            load_devols(i)
        })
    }
}

devol_form_new.cpf.addEventListener('keyup', check_devol)

function check_devol() {
    let cpf = mask_cpfcnpj(devol_form_new.cpf.value)
    devol_form_new.cpf.value = cpf
    cpf=cpf.replace(/\D/g,"")

    if (cpf.length == 11) {
        if (check_cpfcnpj(cpf)) {
            
            fetch(`{{ url_for('auth.get_id') }}?id=${cpf}`)
            .then(response => response.json()).then(data => {
                if (data['result']) {
                    devol_form_new.name.disabled = true
                    devol_form_new.name.value = data['result']['name']
                    devol_form_new.tel.disabled = true
                    devol_form_new.tel.value = mtel(data['result']['tel'])
                    devol_form_new.email.disabled = true
                    devol_form_new.email.value = data['result']['email']
                } else if (data['noresult']) {
                    devol_form_new.name.disabled = false
                    devol_form_new.name.value = ''
                    devol_form_new.tel.disabled = false
                    devol_form_new.tel.value = ''
                    devol_form_new.email.disabled = false
                    devol_form_new.email.value = ''
                } else {
                    data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                }
            })
            .catch(error => { alert(`{{ _('Error in API') }} attend.get_id | ${error}`) })
        } else {
            devol_form_new.cpf.value = devol_form_new.cpf.value.slice(0, -1)
            alert("CPF Inválido")
            return
        }
    } else {
        devol_form_new.name.disabled = true
        devol_form_new.name.value = ''
        devol_form_new.tel.disabled = true
        devol_form_new.tel.value = ''
        devol_form_new.email.disabled = true
        devol_form_new.email.value = ''
    }
}
function save_devol(that) {
    if (devol_form_new.cpf.value.length < 14) {
        alert('Digite cpf valido.')
        return
    }
    if (! devol_form_new.email.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        alert("{{ _('Enter a valid email address') }}")
        return
    }
    if (devol_form_new.prot.value.length < 5) {
        alert('Digite o protocolo valido.')
        return
    }
    if (! devol_form_new.value.value) {
        alert('Digite o valor.')
        return
    }

    let nature = document.querySelector(`#devol_nature_list option[value="${devol_form_new.nature.value}"]`)
    if (! nature) {
        alert('Natureza inválida.')
        return
    }

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let data = {
        'cpf': devol_form_new.cpf.value.replace(/\D/g,""),
        'name': devol_form_new.name.value,
        'email': devol_form_new.email.value,
        'tel': devol_form_new.tel.value,
        'prot': devol_form_new.prot.value,
        'nature': nature.dataset.value,
        'value': devol_form_new.value.value.replace('.', '').replace(',', '.'),
    }

    let api_url = "{{ url_for('finance.post_devol') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( data ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            load_devols('waiting')
            devol_form_new.reset()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        that.innerHTML = btn_html })
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html
    })
}

function confirm_retire(that, id) {
    if (confirm('Confirmar que o cheque está pronto para retirada?')) {
        let btn_html = that.outerHTML
        that.outerHTML = spinner_w
    
        let api_url = "{{ url_for('finance.put_devol') }}"
        fetch(api_url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'retireok': id} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                load_devols('pending')
                devol_modal.hide()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.outerHTML = btn_html }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.outerHTML = btn_html })
    }
}
