window.addEventListener("load", (event) => {
    {% if config.DEBUG %}
        // open_prot_info('661ed63c8c118201dc202301')
    {% endif %}
})

// const all_payments = {{ config['PAYMENTS']|tojson|safe }}
// const all_services = {{ config['SERVICES']|tojson|safe }}

const prot_modal = new bootstrap.Modal(sec_info.querySelector('#prot_info_modal'))
const prot_info_body = sec_info.querySelector('#prot_info_body')

function open_prot_info(id, args=false) {
    let api_url = `{{ url_for('attend.prot_info') }}?id=${id}`
    if (args) api_url += `&${args}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            // if (result.attend) {
                prot = result
                let doc_recebido = []
                let doc_faltante = []
                for (d of result.docs) {
                    if (d.entregue === true) {
                        doc_recebido.push(d)
                    } else {
                        doc_faltante.push(d)
                    }
                }
                // History
                prot_comments = ''
                for (e of result['history']) {
                    switch (e.action) {
                        case 'create':
                            if (e.object === 'service') {
                                text = `<span>Criou o serviço <b>${e.target.prot}</b> no valor de: <b>${e.target.total.toLocaleString('pt-BR', currency_br)}</b></spam>`
                            } else if (e.object === 'exig') {
                                text = `<span>Enviou exigência por <b>email</b>. <a class="btn btn-sm mx-4 btn-outline-secondary" href="{{ url_for('attend.get_exig') }}?id=${e.target.id}&exig=exig" target="_blank" rel="noopener noreferrer"><i class="fas fa-sm fa-download"></i></a></spam>`
                            } else if (e.object === 'docs') {
                                text = `<span>Adicionou <b>documento</b> ao Protocolo <b>${e.target.prot}</b></span>`
                            }
                            break
                        case 'confirm':
                            text = `<span>Confirmou <b>${e.target['type']}</b> no valor de <b>${e.target['value'].toLocaleString('pt-BR', currency_br)}</b>.</spam>`
                            break
                        case 'pay':
                            text = `<span>Pagou a diferença do serviço <b>${e.target['prot']}</b> no valor de <b>${e.target['paying'] ? e.target['paying'].toLocaleString('pt-BR', currency_br) : e.target['total'] ? e.target['total'].toLocaleString('pt-BR', currency_br) : ''}</b>.</spam>`
                            break
                        case 'value':
                            text = `<span>Alterou o <b>valor</b> do protocolo ${e.target.prot} de <b>${e.target.total.toLocaleString('pt-BR', currency_br)}</b> para <b>${e.target.new_value.toLocaleString('pt-BR', currency_br)}</b></spam>`
                            break
                        case 'edit':
                            text = `<span>Alterou o <b>código</b> do protocolo de <b>${e.target.prot}</b> para <b>${e.target.new_cod}</b></spam>`
                            break
                        case 'comment':
                            text = `<span>Adicionou <b>comentário:</b> ${e.target.comment}.</spam>`
                            break
                        default:
                            text = 'Evento <b>desconhecido</b>'
                            break
                    }
                    prot_comments += `
                        <li class="list-group-item list-group-item-action">
                            <div class="item-header">
                                <div class="fw-bold">
                                    ${e.actor.split(' ', 1) + ' ' + e.actor.split(' ').pop()}
                                </div>
                                <div>
                                    <span class="badge bg-primary rounded-pill">${new Date(e.timestamp * 1000).toLocaleString('default', {timeZone: 'America/Sao_Paulo' })}</span>
                                </div>                       
                            </div>
                            <div>
                                ${text}
                            </div>
                        </li>
                    `
                }
                nature_id =  all_natures['attend'][result.type][result.nature].id 
                // prot_total_payments = prot_total_payments.toLocaleString('pt-BR', currency_br)
                // prot_total_paid = prot_total_paid.toLocaleString('pt-BR', currency_br)
                prot_info_body.innerHTML = `{% include "attend/prot/content.html" %}`
    
    
                prot_modal.show()
            // } else {
            //     alert('nha')
            //     open_prot_info(prot.id)
            // }
            
        } else {
            data['error'] ? alert(data['error']) : console.log('Unknown data:', data)
            
        }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                        })
}

function prot_attend_info(that, id) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    open_attend_info(id)
    prot_modal.hide()
}

function info_prot_change() {
    const edit_prot = document.getElementById("prot_save_btn")
    edit_prot.classList.remove("d-none")
}

const prot_info_confirm_edit = async (that, id) => {
        let oparent = that.closest('.prot_modal_content')
        let value = parseFloat(oparent.querySelector('input[name="prot_value"]').value.replace(/[^0-9,.]/g, '').replace('.', '').replace(',', '.'))
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        if (value !== prot.total) {
            if (confirm("Deseja realmente ALTERAR o VALOR do protocolo?")) {
                to_value = {
                    id,
                    value,
                    'action': 'value',
                }
                let api_url = "{{ url_for('attend.put_prot') }}"
                await fetch(api_url, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                    body: JSON.stringify(to_value) })
                .then(response => response.json()).then(data => {
                    if (data['result']) {
                            open_prot_info(id)
                    } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
                            that.innerHTML = btn_html}
                }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                        that.innerHTML = btn_html})
            }
        }
        {% if 'adm' in roles %}
            let cod = oparent.querySelector('input[name="prot_cod"]').value
            if (cod !== prot.prot) {
                if (confirm("Deseja realmente ALTERAR o CÓDIGO do protocolo?")) {
                    to_send = {
                        id,
                        cod,
                        'action': 'edit',
                    }
                    let api_url = "{{ url_for('attend.put_prot') }}"
                    await fetch(api_url, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                        body: JSON.stringify(to_send) })
                    .then(response => response.json()).then(data => {
                        if (data['result']) {
                                open_prot_info(id)
                        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
                                that.innerHTML = btn_html}
                    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                            that.innerHTML = btn_html})
                }
            }
        {% endif %}
}

const exig_prot_attend_info = async (that, id) => {
    let oparent = that.closest('.prot_content_exig')
    let file = oparent.querySelector(`#exig_prot_file`)
    
    // Validações
    if (!file.value.length) {
        alert('Selecione o arquivo')
        return
    }

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let to_send = {
        id,
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
    to_send['file'] = uploads[0]


    let api_url = "{{ url_for('attend.post_exig') }}"
    await fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            prot_modal.hide()
            open_prot_info(id)
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
    that.innerHTML = btn_html})
}

function exig_prot_attend_info_file(that, id){
    let oparent = that.closest('.prot_content_exig')
    let files = oparent.querySelector(`#exig_prot_file`).files
    
    files.innerHTML = ''
    let filename = oparent.querySelector('#exig_prot_file_list')
    filename.innerHTML = ''
    for (const file of files) {
        const li = document.createElement('li');
        li.textContent = file.name;
        li.className = 'list-group-item list-group-item-action'
        filename.appendChild(li)
    }
    oparent.insertAdjacentHTML('beforeend', `
        <button type="button" name="btn"  id="attend_start" class="btn btn-sm btn-outline-success text-center mx-4" onclick="exig_prot_attend_info(this, '${id}')">
            <i class="far fa-sm fa-paper-plane"></i>
        </button>
    `)
}

function info_prot_add_docs(that, id) {

    // let id = that.parentElement.querySelector(`option[value="${that.value}"]`).dataset.value
    
    fetch(`{{ url_for('attend.nature_info') }}?id=${id}`)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            if (result.type === 'prot') {
                let info_attend_new_doc = prot_info_body.querySelector(`#info_attend_new_doc`)
                info_attend_new_doc.innerHTML = `
                    <div>
                        <table class="table table-sm table-hover">
                            <tbody>
                                ${result.docs.map(d => `
                                    <tr>
                                        <td class="d-flex align-items-center justify-content-between">
                                            <div class="btn-group btn-group-sm" role="group">
                                                <input checked type="radio" class="btn-check dispensa" name="${id}_${d.name}" id="dispensa_${d.id}_${id}" autocomplete="off" >
                                                <label class="btn btn-outline-dark" for="dispensa_${d.id}_${id}">
                                                <i class="fas fa-sm fa-ban"></i>
                                                </label>
                                                <input type="radio" class="btn-check entregue" name="${id}_${d.name}" id="entregue_${d.id}_${id}" autocomplete="off" >
                                                <label class="btn btn-outline-success" for="entregue_${d.id}_${id}">
                                                    <b>
                                                        Entregue
                                                    </b>
                                                </label>
                                                <b class="mx-2 d-flex align-items-center">${d.name}</b>
                                            </div>
                                            <div style="max-width:300px;" class="d-flex align-items-center form-check form-switch">
                                            <label class="visually-hidden" for="${id}_qtd"></label>
                                                <input type="number" class="form-control nature-qtd" name="${id}_qtd" value="1"style="max-width:68px;">
                                                <div class="input-group input-group-sm mx-2">
                                                <div class="form-check form-switch">
                                                    <input class="form-check-input nature-doc-copia" type="checkbox" role="switch" name="${id}_copia">
                                                    <label class="form-check-label" for="${id}_copia"><b class="text-danger">Cópia</b></label>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                    <div>
                        <button tabindex="-1" type="button" onclick="info_prot_docs_save(this, '${prot.id}')" class="btn btn-sm my-4 btn-outline-success"><i class="fas fa-sm fa-save"></i></button>
                    </div>
                `
            }
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }})
    .catch(error => {
        alert(`{{ _('Error in API') }}: settings.document ${error}`)
    })
}


function info_prot_comment(that, id) {

    let oparent = that.closest('.prot_info_history')
    let comment = oparent.querySelector('#prot_info_comment').value
    if (!comment) {
        alert('Comentário inválido')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let to_send = {
        id,
        comment,
    }
    let api_url = "{{ url_for('attend.prot_comment') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
                open_prot_info(id)
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
                that.innerHTML = btn_html}
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                        that.innerHTML = btn_html})
}



function info_prot_docs_save(that, id) {
    if (confirm("Deseja realmente ADICIONAR documentos ao protocolo?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = "{{ url_for('attend.put_docs') }}"
        to_send = {
            id,
            'docs': [],
        }
        // Buscar documentos
        let service_docs_elem = that.closest('#info_attend_new_doc')
        service_docs_elem.querySelectorAll('.entregue').forEach(entr => {
            if (entr.checked) {
                let new_doc = {'name': entr.name.split('_')[1], 'entregue': true}
                // Cópia
                let copia = entr.parentElement.parentElement.querySelector('.nature-doc-copia')
                if (copia.checked) new_doc['copia'] = true
                // Quantidade
                let qtd = entr.parentElement.parentElement.querySelector('.nature-qtd').value
                new_doc['qtd'] = parseInt(qtd)
                to_send.docs.push(new_doc)
            }
        })
        fetch(api_url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify(to_send) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_prot_info(id)
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }})
        .catch(error => {
            alert(`{{ _('Error in API') }}: settings.document ${error}`)
            that.innerHTML = btn_html
        })
    }
}

