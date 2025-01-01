document.addEventListener("DOMContentLoaded", (event) => {
    load_attend()
     {% if config.DEBUG %}
        // open_attend_info('677078ffec0022bcfc1851f7')
    {% endif %}
})

const sec_attend = $('attend')
const new_attend = document.forms.new_attend
const cur_attend = document.forms.cur_attend

let attend
let booking_list_start = 0
let booking_list_perpage = 1


// Attend List Datatable
const attend_rowtemplate = (data) => {
    // let paid = data['paid'] + (data['to_pay'] - data['paid'])
    return `
        <tr onclick="open_attend_info('${data['id']}')">
            <td>${new Date(data['end'] * 1000).toLocaleString('default', { dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</td>
            <td>${data['name']}</td>
            <td>${mask_cpfcnpj(data['cpf'])}</td>
        </tr>
    `
}

const attend_table = new DataTable({
    name: 'attend',
    apiEndpoint: "{{ url_for('attend.list') }}",
    headers: ['Data', 'Nome', 'CPF'],
    rowTemplate: attend_rowtemplate,
    spinner: true,
})
attend_table.init(
    '#attend_list_table', '#attend_list_pagination',
    '#attend_list_loading', '#attend_list_error', false,
)

function load_attend() {
    let api_url = "{{ url_for('attend.index') }}"
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            attend = result
            cur_attend.innerHTML = `{% include 'attend/cur_attend.html' %}`
            new_attend.hidden = true
            cur_attend.hidden = false
        } else if (data['noresult']) {
            new_attend.hidden = false
            cur_attend.hidden = true

        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) } })
    .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}


function cancel_attend(that) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    if (confirm("Deseja realmente CANCELAR o atendimento?")) {
        let api_url = "{{ url_for('attend.delete') }}"
        fetch(api_url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'id': cur_attend.id.value.trim()} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                // attend_table.loadItems()
                load_attend()
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

const save_attend = (that) => {

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    
    let to_send = {}
    let erro_form
    cur_attend.querySelectorAll('input').forEach(elem => {
        if(elem.value){
            if(elem.name === 'prot_val' || elem.name === 'prot_tot_c' || elem.name === 'prot_tot_p'){
                to_send[elem.name] = parseFloat(elem.value.replace(/[^\d.,]/g, '').replace('.', '').replace(',', '.'))
            } else if (elem.name === 'prot_emi' || elem.name === 'prot_date' || elem.name === 'prot_ven') {
                // Criar um objeto ajustado para Brasília
                let date = new Date(`${elem.value}T00:00:00-03:00`);
                to_send[elem.name] = date.getTime() / 1000
                // Obter o timestamp (em milissegundos desde 1970)
            } else if (elem.name === 'prot_cod' || elem.name === 'prot_num') {
                to_send[elem.name] = parseFloat(elem.value)
            } else if (elem.name === 'end_cep') {
                to_send[elem.name] = parseFloat(elem.value.replace(/[\D]+/g,''))
            } else if (elem.name === 'id') {
                to_send['attend'] = elem.value
            } else {
                to_send[elem.name] = elem.value
            }
        } else {
            if(elem.name !== 'prot_ven') {
                erro_form = true
                that.innerHTML = btn_html;
                return
            }
        }
    })
    if (erro_form) {
        alert('Preencha todos os campos do formulário')
        return
    }
    let api_url = "{{ url_for('attend.post_service') }}";
    fetch(api_url, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json', 
            "X-CSRFToken": csrf_token 
        },
        body: JSON.stringify(to_send)
    })
    .then(response => {
        if (!response.ok) {
            // Levanta um erro se o status não for 2xx
            return response.json().then(err => {
                throw new Error(err.message || `API error: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        let result = data['result'];
        if (result) {
            load_attend();
            open_attend_info(cur_attend.id.value.trim());
        } else {
            let errorMessage = data['message'] || 'Unknown error occurred.';
            alert(`Error: ${errorMessage}`);
            that.innerHTML = btn_html;
        }
    })
    .catch(error => {
        // Exibe alertas para erros que ocorreram durante a solicitação
        alert(`Erro na API: ${error.message}`);
        that.innerHTML = btn_html;
    });
}

let filter_attend = function(that, filter) {
    from = new_attend.date_start.value
    end = new_attend.date_end.value
    if (end && ! from) {
        alert('Selecione a data inicial.')
        return
    }
    if (from && end && from > end) {
        alert('O dia final não pode ser antes do dia inicial!')
        return
    }

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    if (filter && attend_table.filter !== filter) {
        attend_table.filter = filter
        attend_table.currentPage = 1
    }

    let args = `${from ? `from=${from}` : ''}${end ? `&end=${end}` : ''}`
    attend_table.loadItems(args ? args : false)

    that.innerHTML = btn_html
}

function attend_change_perpage(value) {
    let cur_item = attend_table.perPage * (attend_table.currentPage - 1) + 1
    attend_table.perPage = value
    let new_page = Math.ceil(cur_item / value)
    attend_table.currentPage = new_page
    attend_table.loadItems()
}

new_attend.attend_cpf.addEventListener('keyup', check_attend)
function check_attend() {
    validate = false
    let cpf_cnpj = mask_cpfcnpj(new_attend.attend_cpf.value);
    new_attend.attend_cpf.value = cpf_cnpj
    cpf_cnpj = cpf_cnpj.replace(/\D/g,"");
        if (cpf_cnpj.length === 11) {
                if (check_cpfcnpj(cpf_cnpj)) {
                    new_attend.attend_name.disabled = false
                    validate = true
                } else {
                    new_attend.attend_name.disabled = true
                    new_attend.attend_name.value = ''
                }
        } else if (cpf_cnpj.length === 14) {
                if (check_cpfcnpj(cpf_cnpj)) {
                    new_attend.attend_name.disabled = false
                    validate = true
                } else {
                    new_attend.attend_name.disabled = true
                    new_attend.attend_name.value = ''
                }
        } else {
        }

    if (validate) {
        if (check_cpfcnpj(cpf_cnpj)) {
            let api_url = `{{ url_for('auth.get_id') }}?id=${cpf_cnpj}`
            fetch(api_url)
            .then(response => response.json()).then(data => {
                if (data['result']) {
                    // new_attend.attend_name.disabled = true
                    new_attend.attend_name.value = data['result']['name']
                    // new_attend.attend_email.disabled = true
                } else if (data['noresult']) {
                    // new_attend.attend_name.disabled = false
                    new_attend.attend_name.value = ''
                    // new_attend.attend_email.disabled = false
                } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
            }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
        } else {
            new_attend.attend_cpf.value = new_attend.attend_cpf.value.slice(0, -1)
            alert("{{ _('Invalid CPF / CNPJ') }}")
        }
    }
}

function create_attend() {
    if (! check_cpfcnpj(new_attend.attend_cpf.value)) {
        new_attend.attend_cpf.value = new_attend.attend_cpf.value.slice(0, -1)
        alert("{{ _('Invalid CPF') }}")
        return
    }
    let uid  = new_attend.attend_cpf.value.replace(/\D/g, "")
    let name = new_attend.attend_name.value.trim()
    let api_url = `{{ url_for('auth.get_id') }}?id=${uid}`
    fetch("{{ url_for('attend.new') }}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( {
            'name': name,
            'cpf': uid
            } ) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            load_attend()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
    })
    .catch(error => { alert(`{{ _('Error in API') }} attend.new | ${error}`) })
} 
        
function get_attend_info() {
    // Serviços para enviar
    let services = []
    // Elementos Serviço
    let service_list = $('service_list').children
    for (let i = 0; i < service_list.length; i++) {
        // Service a ser inserido no services
        let service = {
            'type': service_list[i].attributes.type.value,
            'group': service_list[i].attributes.value.value,
            'docs': [],
        }
        // Buscar os elementos do serviço
        let service_info_elem = service_list[i].querySelector('.service-info')
        service_info_elem.querySelectorAll('input').forEach(elem => {
            if (elem.name == 'type') return
            if (elem.type == 'checkbox') {
                service[elem.name] = elem.checked
                return
            }
            if (elem.name == 'natureza') {
                if (Object.keys(all_natures[service.group][service.type === 'repr' || service.type === 'ec' ? 'prot' : service.type ]).includes(elem.value)) {
                    let service_id = elem.attributes.list.value
                    service[elem.name] = document.querySelector(`#${service_id} option[value="${elem.value}"]`).dataset.value
                } else {
                    service[elem.name] = false
                }
                return
            }
            if (elem.name == 'cod') {
                service[elem.name] = elem.value
                return
            } 
            service[elem.name] = parseFloat(elem.value.replace('.', '').replace(',', '.'))
        })

        // Buscar documentos
        let service_docs_elem = service_list[i].querySelector('.service-docs')
        // Elementos marcados


        service_docs_elem.querySelectorAll('.entregue').forEach(entr => {
            if (entr.checked) {
                let new_doc = {'name': entr.name.split('_')[1], 'entregue': true}
                // Cópia
                let copia = entr.parentElement.parentElement.querySelector('.nature-doc-copia')
                if (copia.checked) new_doc['copia'] = true
                // Quantidade
                let qtd = entr.parentElement.parentElement.querySelector('.nature-qtd').value
                new_doc['qtd'] = parseInt(qtd)
                service.docs.push(new_doc)
            }
        })
        service_docs_elem.querySelectorAll('.faltante').forEach(falt => {
            if (falt.checked) {
                let new_doc = {'name': falt.name.split('_')[1], 'entregue': false}
                service.docs.push(new_doc)
            }
        })
        services.push(service)
    }
    let payments = []
    let payment_list = $('payment_list').children
    for (let i = 0; i < payment_list.length; i++) {
        let payment = {}
        payment_list[i].querySelectorAll('span').forEach(elem => {
            payment[elem.attributes['name'].value] = elem.attributes['value'].value
        })
        payments.push(payment)
    }
    return [services, payments]
}


function cur_attend_import_preview(that, type, group) {
    let oparent = that.closest('.cur_attend_import')
    let files = oparent.querySelector('#cur_attend_import_file')
    let filename = oparent.querySelector('#cur_attend_import_file_list')
    let button = oparent.querySelector('.cur_attend_import_btn')
    filename.innerHTML = ''
    const li = document.createElement('li');
    li.textContent = files.files[0].name;
    li.className = 'list-group-item list-group-item-action'
    filename.appendChild(li)
    button.innerHTML = `   <button onclick="cur_attend_import(this, '${type}', '${group}')" type="button" name="btnstart" class="btn btn-sm btn-outline-success text-center">
            <i class="fas fa-sm fa-play-circle"></i>
        </button>
    `
}

const cur_attend_import = async (that, type, group) => {
    let oparent = that.closest('.cur_attend_import')
    let files = oparent.querySelector('#cur_attend_import_file')
    uploads = []
    if (files.files.length) {
        let reader = new FileReader()
        reader.fileName = files.files[0].name
        reader.fileType = files.files[0].type
        reader.fileIndex = files.files[0]
        reader.readAsDataURL(files.files[0])
        reader.onload = () => {
            reader['data'] = reader.result
                .replace('data:', '')
                .replace(/^.+,/, '')
        }
        uploads.push(reader)
        // return
    }
    const load_dili_files = await loop_files(uploads)
    let to_send = {
        'id': attend.id,
        'files': uploads,
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let api_url = "{{ url_for('attend.import_service') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        if (data) {
            let recibo = {
                'prot': data.ordem ? data.ordem : data.attend,
                'total': parseFloat(data.pago) + parseFloat(data.restante),
                'paid': parseFloat(data.pago),
            }
            add_service(type, group, service=false)
            let svc_list = sec_attend.querySelector('#service_list') 
            let svc_elm = svc_list.lastElementChild
            for (i of svc_elm.querySelectorAll('input')) {
                if (i.name === 'cod') {
                    i.value = recibo.prot
                    i.disabled = true
                }
                if (i.name === 'val') {
                    i.value = recibo.total.toLocaleString('pt-BR', currency_br)
                    mask_value(i)
                    i.disabled = true
                }
                if (i.name === 'val_pg') {
                    i.value = recibo.paid.toLocaleString('pt-BR', currency_br)
                    mask_value(i)
                    i.disabled = true
                }
            }
            calc_services()
            that.innerHTML = btn_html
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
                that.innerHTML = btn_html}
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                        that.innerHTML = btn_html})
}

const end_attend = async function (that) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let [services, payments] = get_attend_info()
    if (services.length) {
        for (s of services) {
            if (s.type === 'cert' ) {
                if ( String(s['cod']).length < 17 ) {
                    alert('Protocolo inválido')
                    that.innerHTML = btn_html
                    return
                }  
               
            } else if ( String(s['cod']).length < 5 ) {
                    alert('Protocolo inválido')
                    that.innerHTML = btn_html
                    return
            }  
            // ! Validar natureza
            if (! s['natureza']) {
                alert('Natureza inválida')
                that.innerHTML = btn_html
                return
            }
        }

    } else {
        alert('Adicione um serviço')
        that.innerHTML = btn_html
        return
    }
    let comment = cur_attend.querySelector('.comment')
    let data = {
        'action': 'end',
        'id': cur_attend.id.value.trim(),
        'services': services,
        'payments': payments,
        'comment': comment.value,
    }
    let file = cur_attend.querySelector('.attend_file')

    if (file.files.length) {
        // Para cada arquivo do input criar um item na lista uploads
        let uploads = []
        for (var i = 0; i < file.files.length; i++) {
            let reader = new FileReader()
            reader.fileName = file.files[i].name
            reader.fileType = file.files[i].type
            reader.fileIndex = i
            reader.readAsDataURL(file.files[i])
            reader.onload = () => {
                reader['data'] = reader.result
                    .replace('data:', '')
                    .replace(/^.+,/, '')
            }
            uploads.push(reader)
        } 
        const load_dili_files = await loop_files(uploads)
        data['files'] = uploads
    } 
    let api_url = "{{ url_for('attend.edit') }}"
    fetch(api_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(data) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            load_attend()
            get_attend_balance_info(args=false)
            open_attend_info(cur_attend.id.value.trim())
            // attend_table.loadItems()
            new_attend.reset()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
                that.innerHTML = btn_html}
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                        that.innerHTML = btn_html})
}

const confirm_attend_cred = (that, attend) => {
    let company = cur_attend.cur_attend_cred.value
    if (! company) {
        alert('Informe a empresa credênciada que deseja vincular ao atendimento.')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    to_send = {
        'id': attend,
        'company': company,
    }
    let api_url = "{{ url_for('attend.put_company') }}"
    fetch(api_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            load_attend()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
    that.innerHTML = btn_html})
}


function calc_services() {
    let [services, payments] = get_attend_info()
    let total = 0.0
    let to_pay = 0.0
    let rest = 0.0
    let devols = 0.0
    let diff = cur_attend.querySelector('#payment_diff')
    let nopay = false


    services.forEach(s => {
        if (all_services[s.type]['nopay']) {
            nopay = true
            total += 0.0
            to_pay += 0.0
        }
        total += s['val']
        to_pay = parseFloat((to_pay + s['val_pg']).toFixed(2))
        'val_devol' in s ? devols = devols + s['val_devol'] : ''
    })
    
    cur_attend.querySelector('#payment_total').innerHTML = total.toLocaleString('pt-BR', currency_br)
    cur_attend.querySelector('#payment_topay').innerHTML = parseFloat(to_pay - devols).toLocaleString('pt-BR', currency_br)
    let total_paid = parseFloat(devols)
    rest = parseFloat(to_pay - devols - total)
    payments.forEach(p => {
        if (!all_payments[p.type].pending) {
            total_paid += parseFloat(p.value) 
        } else {
            rest += parseFloat(p.value)
        }
    })
    cur_attend.querySelector('#payment_rest').innerHTML = rest.toLocaleString('pt-BR', currency_br)
    if ((to_pay >= 0 || nopay) && parseFloat((to_pay - total_paid - attend.balance).toFixed(2)) <= 0) {
        sec_attend.querySelector('.cancel_attend').outerHTML = `<button name="btn" type="button" class="btn btn-sm btn-outline-success started cancel_attend" onclick="end_attend(this)" role="button">{{ _('Finalize') }} <i class="far fa-stop-circle"></i></button>`
        diff.parentElement.classList.remove('text-danger')
        diff.parentElement.classList.add('text-success')
    }  else {
        sec_attend.querySelector('.cancel_attend').outerHTML = `<button name="btn" type="button" class="btn btn-sm btn-outline-danger cancel_attend" onclick="cancel_attend(this)" role="button">{{ _('Cancel') }} <i class="far fa-sm fa-times-circle"></i></button>`
        diff.parentElement.classList.remove('text-success') 
        diff.parentElement.classList.add('text-danger')
    }
    diff.innerHTML = (to_pay - total_paid - attend.balance).toLocaleString('pt-BR', currency_br)
}

function attend_service_info(that) {
    that.closest('.g-1').insertAdjacentHTML('beforeend', `
    <div class="col-md-12">
        <div class="form-floating">
            <input tabindex="0" type="text" name="${that.name}" class="form-control form-control-sm" placeholder="">
            <label class="capitalize" for="${that.name}">${that.name}</label>
        </div>
    </div>
    `)
    that.disabled = true
}

function add_payment(that) {
    let select = that.parentElement.querySelector('select')
    let value_e = that.parentElement.querySelector('input')
    if (select.selectedIndex > 0) {
        let value = parseFloat(value_e.value.replace('.', '').replace(',', '.'))
        let p = {
            'type': select.value,
            'value': value,
        }
        let deb = ''
        if ( p.type === 'cd' ) {
            deb =  add_payment_percent(p.value, 0.55) + p.value
        }
        $('payment_list').insertAdjacentHTML('beforeend', `{% include 'attend/payment.html' %}`)
        select.selectedIndex = 0
        value_e.value = ''
        select.focus()
        calc_services()
    }
}

function rest_pay() {
    let rest = document.getElementById("payment_rest").innerHTML

    if(rest.includes('-')) {
        rest = rest.replace('-R$&nbsp;', '')
    } else {
        rest = rest.replace('R$&nbsp;','')
    }

    document.getElementById("default_value").value = rest
}

function diff_pay() {
    let diff = document.getElementById("payment_diff").innerHTML

    if(diff.includes('-')) {
        diff = diff.replace('-R$&nbsp;', '')
    } else {
        diff = diff.replace('R$&nbsp;','')
    }

    document.getElementById("default_value").value = diff
}

function select_service (type) {
    let group_list = sec_attend.querySelector('#service_group_list') 
    group_list.innerHTML = `
        <div class="cur_attend_service_add">
            <div class="service_add_items" onclick="add_service('${type}', 'ri')">
                <b>
                    RI
                </b>
            </div>
            <div class="service_add_items" onclick="add_service('${type}', 'rc')">
                <b>
                    RC
                </b>
            </div>
            <div class="service_add_items" onclick="add_service('${type}', 'rtd')">
                <b>
                    RTD
                </b>
            </div>
        </div>
        <div class="cur_attend_import">
        <div>
          <input type="file" onchange="cur_attend_import_preview(this, '${type}', 'ri')" id="cur_attend_import_file" name="cur_attend_import_file" accept=".jpg,.jpeg,.png,.gif,.pdf,.p7s" style="display: none;">
          <label tabindex="0" class="btn m-2 btn-sm btn-outline-primary" for="cur_attend_import_file">
            <i class="fas fa-sm fa-upload"></i> Importar Arquivo
          </label>
        </div>
        <ol class="list-group list-group-numbered mx-4" id="cur_attend_import_file_list"></ol>
        <div class="cur_attend_import_btn"></div>
        </div>
    `
}

let service_count = 0
function add_service(type, group, service=false) {
    let service_list = sec_attend.querySelector('#service_list') 
    // Sempre o ultimo elemento com name cod
    switch (type) {
        case 'prot':
            service_list.insertAdjacentHTML('beforeend', `{% include 'attend/info/service_prot.html' %}`)
            break
        case 'cert':
            service_list.insertAdjacentHTML('beforeend', `{% include 'attend/info/service_cert.html' %}`)
            break
        case 'repr':
            service_list.insertAdjacentHTML('beforeend', `{% include 'attend/info/service_repr.html' %}`)
            break
        case 'ec':
            service_list.insertAdjacentHTML('beforeend', `{% include 'attend/info/service_ec.html' %}`)
            break
        default:
            alert('Tipo de serviço inválido')
            return
            break
    }
    service_count += 1
    let svc_elm = service_list.lastElementChild
    if (service) {
        if (service.docs.length) {
            let entregue = ''
            let faltante = ''

            for (d of service.docs) {
                if (d.entregue) {
                    entregue += `<a class="list-group-item list-group-item-action list-group-item-success"><b>${d.name}</b><a>`
                } else {
                    faltante += `<a href="" class="list-group-item list-group-item-action list-group-item-danger"><b>${d.name}</b><a>`
                }
            }  

            svc_elm.insertAdjacentHTML('beforeend',
            `  
                <h5 class='py-2'>Documentos Entregues</h5>
                <ul style="max-width: 50%; margin: 0 auto;" class="list-group">
                    ${entregue}
                </ul>
                ${faltante ? `
                    <div class='d-flex justify-content-center gap-1 py-2'>
                        <h5>Documentos Faltantes</h5>
                        <a id=${service.id} class='btn btn-sm btn-danger' onclick='attend_qrcode(this)'> <i class='fas fa-sm fa-upload'></i> </a>
                   </div>
                    <ul style="max-width: 50%; margin: 0 auto;" class="list-group">
                        ${faltante}
                    </ul>
                ` : ''}
            `)
        }

        for (i of svc_elm.querySelectorAll('input')) {
            i.disabled = true
            if (i.name === 'cod') {
                i.value = service.prot
            }
            if (i.name === 'val') {
                i.value = service.total.toLocaleString('pt-BR', currency_br)
                mask_value(i)
            }
            if (i.name === 'val_pg') {
                i.value = service.paid.toLocaleString('pt-BR', currency_br)
                mask_value(i)
            }
            if (i.name === 'natureza') {
                i.value = service.nature
            }
        }
        for (i of svc_elm.querySelectorAll('button')) {
            if(i.classList.contains('del-service')) {
                i.addEventListener("click", () => del_cur_service(service.id, attend.id, svc_elm))
            } else {
                i.disabled = true
            }
        }
    } else {
        sec_attend.querySelector('.cur_attend_content').style.display = "none"
    }
    svc_elm.querySelector('.cod').focus()
    calc_services()
}

function attend_qrcode(that) {
    let btn_default = that.innerHTML
    that.innerHTML = spinner_w

    let api_url = `{{ url_for('attend.get_docs_qrcode') }}?id=${that.id}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        result = data['result']
        if(result) {
            sec_attend.insertAdjacentHTML('beforeend', 
            `
                <div id="myModal" class="modal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                            <h5 class="modal-title"> Leia o QRCode para enviar os arquivos </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <img src="data:image/jpeg;base64,${result}">
                            </div>
                        </div>
                    </div>
                </div>
            `
            )
            const qrcode_modal = new bootstrap.Modal(document.getElementById('myModal'))
            qrcode_modal.show()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        }).catch(error => {
            alert(`{{ _('Error in API') }}: auth.login ${error}`)
            location.reload()
        }).finally(() => {
            that.innerHTML = btn_default
        })
}

function attend_start_enter(event) {
    event.preventDefault()
    if (event.key === 'Enter') { 
        document.getElementById("attend_start").click()
    }
}

function pay_enter(event) {
    event.preventDefault()
    if (event.key === 'Enter') { 
    }
}

function add_service_enter(event) {
    if (event.key === 'Enter') {
      add_service()
    }
}

function add_pay_enter(event) {
    
    if (event.key === 'Enter') {
        document.getElementById("add_pay").click()
    }
}


function attend_file_preview(event){
    if(event.target.files.length > 0){
        let preview = $("attend_file_preview")
        preview.innerHTML = ''
        let img = document.createElement("img")
        Object.assign(img, {
            className: 'img-fluid',
            src: URL.createObjectURL(event.target.files[0]),
            width: 800
        })
        preview.appendChild(img)
    }
}

function next_input_value(that) {
    let inputs = document.getElementsByTagName('input')
    for (i = 0 ; i < inputs.length; i++) {
        if (inputs[i] == that) {
            inputs[i + 1].value = that.value
            return
        }
    }
}

function add_service_docs(that, count) {

    let datalist = that.parentElement.querySelector('datalist')

    let id = that.parentElement.querySelector(`option[value="${that.value}"]`).dataset.value
    
    fetch(`{{ url_for('attend.nature_info') }}?id=${id}`)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            if (result.type === 'prot') {
                let attend_nature_docs = cur_attend.querySelector(`#attend_nature_docs_${count}`)
                attend_nature_docs.innerHTML = `
                    <div style="margin: 30px auto;" class="accordion-item col-md-10 accordion-border attend_doc">
                        <h6 class="accordion-header" id="attend_doc_list_${count}">
                        <button class="accordion-button collapsed text-center" type="button" data-bs-toggle="collapse" data-bs-target="#attend_doc_accordion_content_${count}" aria-expanded="false" aria-controls="attend_doc_accordion_content_${count}">
                            <h5 class="accordion_title">Documentos Vinculados</h5>
                        </button>
                        </h6>
                        <div id="attend_doc_accordion_content_${count}" class="accordion-collapse collapse show" aria-labelledby="attend_doc_list_${count}" data-bs-parent="#attend_doc_accordion_content_${count}">
                            <div class="accordion-body">
                                <table class="table table-sm table-hover">
                                    <tbody>
                                        ${result.docs.map(d => `
                                            <tr>
                                                <td class="d-flex align-items-center justify-content-between">
                                                    <div class="btn-group btn-group-sm" role="group">
                                                        <input checked type="radio" class="btn-check dispensa" name="${count}_${d.name}" id="dispensa_${d.id}_${count}" autocomplete="off" >
                                                        <label class="btn btn-outline-dark" for="dispensa_${d.id}_${count}">
                                                        <i class="fas fa-sm fa-ban"></i>
                                                        </label>
                                                                                            
                                                        <input type="radio" class="btn-check faltante" name="${count}_${d.name}" id="faltante_${d.id}_${count}" autocomplete="off">
                                                        <label class="btn btn-outline-danger mx-2" for="faltante_${d.id}_${count}">
                                                            <b>
                                                                Faltante
                                                            </b>
                                                        </label>
                                                        <input type="radio" class="btn-check entregue" name="${count}_${d.name}" id="entregue_${d.id}_${count}" autocomplete="off" >
                                                        <label class="btn btn-outline-success" for="entregue_${d.id}_${count}">
                                                            <b>
                                                                Entregue
                                                            </b>
                                                        </label>
                                                        <b class="mx-2 d-flex align-items-center">${d.name}</b>
                                                    </div>
                                                    <div style="max-width:300px;" class="d-flex align-items-center form-check form-switch">
                                                    <label class="visually-hidden" for="${count}_qtd"></label>
                                                        <input type="number" class="form-control nature-qtd" name="${count}_qtd" value="1"style="max-width:68px;">
                                                        <div class="input-group input-group-sm mx-2">
                                                        <div class="form-check form-switch">
                                                            <input class="form-check-input nature-doc-copia" type="checkbox" role="switch" name="${count}_copia">
                                                            <label class="form-check-label" for="${count}_copia"><b class="text-danger">Cópia</b></label>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                                <div class="col">
                                    <button type="button" name="btn" class="btn btn-sm btn-success text-center m-3" onclick="save_service(this)">
                                        <i class="fas fa-sm fa-save"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>`
            } else {
                let attend_nature_docs = cur_attend.querySelector(`#attend_nature_docs_${count}`)
                attend_nature_docs.innerHTML = `
                <div class="col">
                    <button type="button" name="btn" class="btn btn-sm btn-success text-center m-3" onclick="save_service(this)">
                        <i class="fas fa-sm fa-save"></i>
                    </button>
                </div>`
            }
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }})
    .catch(error => {
        alert(`{{ _('Error in API') }}: settings.document ${error}`)
    })
}



let del_cur_service = (service, attend, oparent)=> {
    
    let to_send = {
        'id': attend,
        'service': service,
    }

    let api_url = "{{ url_for('attend.del_prot') }}"
    fetch(api_url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            oparent.remove()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }})
    .catch(error => {
        alert(`{{ _('Error in API') }}: settings.document ${error}`)
    })

}

