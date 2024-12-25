window.onload = function () {
    {% if visita %}
        open_itm_info('{{ visita }}')
    {% endif %}
    load_itms()
    // draw_chart_itm()
    load_itm()
    new_itm_cod.focus()
    load_estados()
}



const sec_onr = $('onr')
sec_onr.innerHTML = `{% include 'itm/itm.html' %}`

const cur_itm_modal = new bootstrap.Modal(sec_info.querySelector('#cur_itm_info_modal'))
const cur_itm_info_body = sec_info.querySelector('#cur_itm_info_body')
let itm_people = null

// ITM List
const itm_rowtemplate = (data) => {
    const html = `
        <tr onclick="open_itm_info('${data.id}')">
            <td><b>${data.cod}</b></td>
            <td>${data['payments'].reduce((a,b) => a += ( b.value ), 0).toLocaleString('pt-BR', currency_br)}</td>
            <td>${new Date(data.prot_date * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</td>
        </tr>
    `;
    return html;
};
const itm_table = new DataTable({
    name: 'itm',
    apiEndpoint: '{{ url_for('itm.list') }}',
    headers: ['Pedido', 'Total', 'Data'],
    rowTemplate: itm_rowtemplate,
    spinner: true,
});
itm_table.init('#itm_list_table', '#itm_list_pagination', '#itm_update_btn', '#itm_list_error', );
{% if 'itm-sign' in roles %}
    let = itm_table.filter = 'Assinar'
{% elif 'adm' in roles %}
    let = itm_table.filter = 'Visita-1'
{% else %}
    let = itm_table.filter = 'created'
{% endif %}

google.charts.load('current',{packages:['corechart']})


function itm_change_perpage(value) {
    let cur_item = itm_table.perPage * (itm_table.currentPage - 1) + 1
    itm_table.perPage = value
    let new_page = Math.ceil(cur_item / value)
    itm_table.currentPage = new_page
    load_itms()
}

function add_itm_p() {
    itm_people.insertAdjacentHTML('beforeend', `
        <div class="itm_people_item">
            <i class="fas fa-sm fa-user mx-2"></i> Devedor
            <button type="button" name="btn" class="btn btn-sm btn-danger text-center" onclick="this.closest('.itm_people_item').remove();">
                <i class="fas fa-sm fa-user-minus"></i>
            </button>
        </div>`
    )
    get_municipios(itm_people.lastElementChild.querySelector('.estado'))
}

function get_municipios(that) {
    let uf = that.value
    let select = that.parentElement.nextElementSibling.querySelector('select')
    select.innerHTML = ''
    let api_url = `{{ url_for('base.get_uf') }}?uf=${uf}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let municipios = data['result']
        if (municipios) {
            municipios.sort().map(mun => {
                let opt = document.createElement("option")
                opt.value = mun
                opt.text = mun
                if (mun == 'Cidade Ocidental') {
                    opt.selected = true
                }
                select.add(opt)
            })
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}


function load_estados() {
    let api_ufs = "{{ url_for('base.get_ufs') }}"
    fetch(api_ufs)
    .then(response => response.json()).then(data => {
        if (data['result']) {
            estados = data['result']
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_ufs} | ${error}`) })
}

let start_itm = async function (that){
    // Validações
    let file = sec_onr.querySelector('#itm_file') 
    if (!file.value.length) {
        alert('Selecione os arquivos')
        return
    }


    let form = sec_onr.querySelector('#new_itm')
    let cod = form.itm_cod.value

    if (cod.length != 11) {
        alert("{{ _('Invalid Code') }}")
        that.innerHTML = btn_html
        return
    }
    if (! form.itm_date.value) {
        alert('Selecione uma data!')
        that.innerHTML = btn_html
        return
    }

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let to_send = {
        'type': 'onr',
        'cod': cod.trim().toUpperCase(),
        'prot_date': form.itm_date.value,
    }

    // Para cada arquivo do input criar um item na lista uploads
    uploads = []
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
    to_send['files'] = uploads


    let api_url = "{{ url_for('itm.post') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            load_itm()
            that.innerHTML = btn_html
        } else if (data['noresult']) {
            alert(data['noresult'])
            if (confirm('Deseja gravar assim mesmo?')) {
                let n_pessoas = prompt('Digite a quantidade de pessoas')
                if (isNaN(n_pessoas) || n_pessoas < 1 || n_pessoas > 3) {
                    alert('Número inválido')
                    that.innerHTML = btn_html
                    return
                }
                to_send['force'] = true
                to_send['pessoas'] = n_pessoas
                fetch(api_url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                    body: JSON.stringify(to_send) })
                .then(response => response.json()).then(data => {
                    if (data['result']) {
                        load_itm()
                        that.innerHTML = btn_html
                    } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                            that.innerHTML = btn_html }
                }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
                that.innerHTML = btn_html})
            }
            that.innerHTML = btn_html
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
    that.innerHTML = btn_html})
}

async function draw_chart_itm() {
    let chart_id = sec_onr.querySelector('#chart_itm')
    let api_url = "{{ url_for('itm.get_status') }}"

    await fetch(api_url)
        .then(response => response.json()).then(data => {
            let result = data['result']
            if (result) {

                let dt = [
                    ['Element', 'Quantidade', { role: 'style' } ],
                ]
                let colors = ['#b87333', 'silver', '#2a6b04', '#e5e4e2', 'red']
                for (i of result) {
                    dt.push([i[0], i[1], colors.pop()])
                }

                let data = google.visualization.arrayToDataTable(dt)

                let options = {
                    'title': 'Resumo das etapas',
                    'width': 1280,
                    'height': 360,
                    'bar': {groupWidth: '56%'},
                    'legend': { position: 'none' },
                }

                let view = new google.visualization.DataView(data);
                view.setColumns([0, 1,
                                { calc: 'stringify',
                                sourceColumn: 1,
                                type: 'string',
                                role: 'annotation' },
                                2]);

                let chart = new google.visualization.ColumnChart(chart_id)
                chart.draw(view, options)

                function selectHandler(e) {
                    load_itms(result[chart.getSelection()[0].row][0])
                }
                google.visualization.events.addListener(chart, 'select', selectHandler)


            } else {
                data['error'] ? alert(data['error']) : console.log('Unknown data:', data)
            } })
        .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
        .finally(() => { 

        })
}


function load_itms(filter=false) {
    if (filter && filter !== itm_table.filter) {
        itm_table.filter = filter
        itm_table.currentPage = 1
    }
    draw_chart_itm()
    itm_table.loadItems()
}

function filter_itms_enter(event) {
    event.preventDefault()
    if (event.key === 'Enter') { 
        sec_onr.querySelector('#filter_itms_btn').click()
    }
}


let new_itm_file = sec_onr.querySelector('#itm_file')
new_itm_file.addEventListener('change', (event) => {
    const files = event.target.files
    let filename = sec_onr.querySelector('#itm_file_list')
    filename.innerHTML = ''
    for (const file of files) {
        const li = document.createElement('li');
        li.textContent = file.name;
        li.className = 'list-group-item list-group-item-action'
        filename.appendChild(li)
    }
})

let new_itm_form = sec_onr.querySelector('#new_itm') 
const itm_update_elem = sec_onr.querySelector(`#itm_update_btn`)
const itm_update_html = itm_update_elem.innerHTML

new_itm_form.itm_date.value = (new Date(Date.now() - (new Date()).getTimezoneOffset() * 60000)).toISOString().slice(0, 10)


let itm_service_list = ''
let service_itm_count = 2
function load_itm(){
    let api_url = "{{ url_for('itm.get') }}"
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            cur_itm_info_body.innerHTML = spinner_b
            cur_itm_modal.show()

            let devedor = ''
            if (result['pessoas']) {
                if (result.pessoas.length <=1) {
                    devedor += '<h4 class="my-3">Devedor(a)</h4>'
                }  else {
                    devedor += '<h4 class="my-3">Devedores(as)</h4>'
                }
                devedor += result.pessoas.map(p => 
                    `<div><h6><b>${p.name ? p.name : 'Nome não identificado'}</b> - ${mask_cpfcnpj(p.cpf)}</h6><div>`).join('')
            }

            let credor = ''
            if (result['credor']) {
                credor = `
                    <h4 class="my-3">Credor</h4>
                    <h6><b></b>${result['credor'].name} - ${result['credor'].cnpj}<br>${result['credor'].sede}</h6>
                `
            }

            let enderecos = ''
            if (result['enderecos']) {
                if (Object.values(result['enderecos']).length > 0 ) {
                    enderecos += `<h5 class="my-3">Endereços de intimação</h5>`
                }
                Object.values(result['enderecos']).forEach(e => { 
                    enderecos += `<div><h6><b>${e.end} ${e.municipio ? e.municipio : ''}/${e.estado}</b> <br> CEP: ${e.cep}</h6></div>`
                })
            }
            cur_itm_info_body.innerHTML = `{% include 'itm/cur_itm.html' %}`
            itm_service_list = cur_itm_info_body.querySelector('#itm_service_list')
            itm_service_list.insertAdjacentHTML('beforeend', `{% include 'itm/service_prot.html' %}`)
            service_itm_count += 1
            Array.from(Array(result.pessoas.length).keys()).forEach(p => {
                itm_service_list.insertAdjacentHTML('beforeend', `{% include 'itm/service_c_dil.html' %}`)
                service_itm_count += 1
            })
            itm_service_list.insertAdjacentHTML('beforeend', `{% include 'itm/service_c_dec.html' %}`)
            service_itm_count += 1
            // check_itm()
        } else { data['error'] ? alert(data['error']) : '' }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}

function check_itm(end = false) {
    let services = []
    let zero = false
    let form = sec_onr.querySelector('#cur_itm')
    return {
        'id': form.id.value,
        'services': services,
        'comment': form.comment.value.trim(),
    }
}

function cancel_itm(that) {
    let form = cur_itm_info_body.querySelector('#cur_itm')
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    if (confirm("Deseja realmente CANCELAR a intimação?")) {
        let api_url = "{{ url_for('itm.delete') }}"
        fetch(api_url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'id': form.id.value.trim()} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                cur_itm_modal.hide()
                // load_itm()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html
        })
    } else {
        that.innerHTML = btn_html
    }
}

function confirm_pay_itm(that, id, itm) {
    if (confirm('Deseja realmente CONFIRMAR o pagamento?')) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.put_payment') }}`
        fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify({
                        'action': 'confirm', 
                        id,
                        itm,})})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(result)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url}`) 
        that.innerHTML = btn_html})    
    }
}


let uploads = []

var orc_itm = async function(that) {
    // Validações

    let form = cur_itm_info_body.querySelector('#cur_itm')
    let itm_data = {
        'id': form.id.value,
        'comment': form.comment.value.trim(),
    }

    let btn_start = cur_itm_info_body.querySelector('.started')
    let btn_html = btn_start.innerHTML
    btn_start.innerHTML = spinner_w

    let api_url = "{{ url_for('itm.orcar') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( itm_data ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            cur_itm_modal.hide()
            load_itms()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            btn_start.innerHTML = btn_html }})
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        btn_start.innerHTML = btn_html })
}


function del_itm(that, id){
    if (confirm('Deseja realmente DELETAR a intimação?')) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.delete') }}`
        fetch(api_url, {method: 'DELETE',
                        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                        body: JSON.stringify( {'id': id} ) })
        .then(response => response.json()).then(data => {
            if (data['result']) {
                itm_modal.hide()
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                    that.innerHTML = btn_html }
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html})
    }
}


function disabled_itm(that, id){
    if (confirm('Deseja realmente FINALIZAR a intimação?')) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        return
        let api_url = `{{ url_for('itm.delete') }}`
        fetch(api_url, {method: 'DELETE',
                        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                        body: JSON.stringify( {'id': id} ) })
        .then(response => response.json()).then(data => {
            if (data['result']) {
                itm_modal.hide()
                load_itm()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                    that.innerHTML = btn_html }
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html})
    }
}

function add_itm_file(that) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let itm_file = $('itm_info_file')

    itm_file.insertAdjacentHTML('beforeend', `
        <tr class="itm_file">
            <td></td>
            <td>name</td>
            <td><button tabindex="-1" type="button" class="btn btn-sm btn-outline-danger" onclick="this.closest('.itm_file').remove()"><i class="fas fa-sm fa-trash"></i></button></td>
        </tr>
    `)
    that.innerHTML = btn_html
}
