window.addEventListener("load", (event) => {
    {% if config.DEBUG %}
        // open_itm_info('655de90050d9ff462c03566b')
    {% endif %}
})

const cur_itm = $('cur_itm')
const info_itm = $('itm_info_modal')

const itm_modal = new bootstrap.Modal(sec_info.querySelector('#itm_info_modal'))
const itm_info_body = sec_info.querySelector('#itm_info_body')

let estados = []
const estado_loaded = {}

let info_itm_count = 0

let intimacao = []
let itm_pessoas = []
const credores = {{ credores|tojson|safe }}

async function fill_minuta_municipios(that) {
    let uf = that.value.toUpperCase()
    let select = that.parentElement.previousElementSibling.querySelector('datalist')

    select.innerHTML = ''
    if (! Object.keys(estado_loaded).includes(uf)) {
        let api_url = `{{ url_for('base.get_uf') }}?uf=${uf}`
        // await fetch(api_url)F
        fetch(api_url)
        .then(response => response.json()).then(data => {
            let municipios = data['result']
            if (municipios) {
                estado_loaded[uf] = municipios
                select.insertAdjacentHTML('beforeend', estado_loaded[uf].sort().map(mun => `<option data-value="${ mun }" value="${ mun }"></option>`).join(''))
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
    }
}

function itm_render_payments(list) {
    let result = ''
    for (l of list) {
        if (l.type === 'Onr') {
            result += `<tr>
                <td><i class="fas text-success fa-chevron-circle-up"></i></i></td>
                <td>${l['confirmed'] ? `<i class="fas text-primary fa-sm fa-check"></i>` : `<button tabindex="-1" type="button" title="Confirmar pagamento" class="btn btn-sm ms-2 btn-outline-success" onclick="confirm_pay_itm(this, '${l['id']}', '${intimacao.id}')"><i class="fas fa-sm fa-dollar-sign"></i></button>`}</td>
                <td>${new Date(l['timestamp'] * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</td>
                <td style="text-align: end;">${l['value'].toLocaleString('pt-BR', currency_br)}</td>
            </tr>`
        } else {
            result += `<tr>
                <td><i class="fas text-danger fa-chevron-circle-down"></i></i></td>
                <td><i class="fas fa-sm text-primary fa-check"></i></td>
                <td>${new Date(l['timestamp'] * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</td>
                <td style="text-align: end;">- ${l['paid'].toLocaleString('pt-BR', currency_br)}</td>
            </tr>`
        }
    } 
    return result
}

function open_itm_info(id) {
    itm_info_body.innerHTML = spinner_b
    itm_modal.show()
    let api_url = `{{ url_for('itm.get_info') }}?id=${id}`
    let about = 'then'
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        itm_pessoas = []
        if (result) {
            about = 'result'
            intimacao = result
            console.log(result)
            let matricula = result.mat
            let saldo = result['payments'].reduce((a,b) => a += (b.confirmed ? b.value : 0) , 0).toFixed(2)
            let total = result['payments'].reduce((a,b) => a += (b.value), 0).toFixed(2)
            let total_serv = result['services'].reduce((a,b) => a += (b.value), 0).toFixed(2)
            let gasto = result['services'].reduce((a,b) => a += (b.paid), 0).toFixed(2)
            saldo = (saldo - gasto).toFixed(2)
            total_serv = data['total'] + data['prot_values']['cert'] + (data['prot_values']['cert'] * intimacao.pessoas.length)
            let disabled = ''

            if (intimacao.services[0] && intimacao.services[0].minuta) {
                disabled = 'disabled'
            }
            // History
            about = 'History'
            itm_comments = ''
            for (e of result['history']) {
                switch (e.action) {
                    case 'comment':
                        text = `<span>Adicionou <b>comentário</b>: ${e.target['comment']}</span>`
                        break
                    case 'budget':
                        text = `<span>Criou o <b>serviço</b> no valor de: <b>${e.target['value'].toLocaleString('pt-BR', currency_br)}</b></span>.`
                        break
                    case 'confirm':
                        if (e.object === 'minuta') {
                            text = `<span>Aprovou a <b>Minuta</b>.</span>`
                        } else {
                            text = `<span>Confirmou <b>pagamento</b> no valor de: </span><b>${e.target['value'].toLocaleString('pt-BR', currency_br)}</b>.</span>`
                        }
                        break
                    case 'create':
                        if (e.object == 'service') {
                            text = `<span>Pagou o serviço <b>${e.target.prot}</b> no valor de: <b>${e.target.paid.toLocaleString('pt-BR', currency_br)}</b></span>`
                        } else if (e.object == 'visita') {
                            text = `<span>Visitou <b>${e.target.visita.dev}</b> no dia <b>${new Date(e.target.visita.date * 1000).toLocaleString('default', {timeZone: 'America/Sao_Paulo' })}</b> com resultado "${ e.target.visita.result == 'p' ? '<b class="text-success fw-bold">Positiva</b>' : e.target.visita.result == 'n' ? '<b class="text-danger fw-bold">Negativa</b>' : e.target.visita.result == 'r' ? '<b class="text-primary fw-bold">Recusou</b>' : e.target.visita.result == 'f' ? '<b class="fw-bold">Falecido</b>' : e.target.visita.result == 'd' ? '<b class="text-warning fw-bold">Outros</b>' : e.target.visita.result == 'i' ? '<b class="text-danger fw-bold">Incorreto</b>' : e.target.visita.result == 'm' ? '<b class="text-info">Mudou</b>' : e.target.visita.result == 'c' ? '<b class="text-secondary">Cartório</b>' : ''}".</span>`
                        }
                        break
                    case 'pay':
                        if (e.object == 'service') {
                            text = `<span>Pagou o restante do serviço <b>${e.target.prot}</b> no valor total de: <b>${e.target.total.toLocaleString('pt-BR', currency_br)}</b></span>`
                        }
                        break
                    case 'minuta':
                        text = `<span>Cadastrou nova <b>minuta</b>.</span>`
                        break
                    case 'edit':
                        text = `<span>Editou a <b>Minuta</b>.</span>`
                        break
                    case 'print':
                            text = `<span>Marcou como <b>Impresso</b>.</span>`
                            break
                    case 'reject':
                        text = `<span>Rejeitou a <b>Minuta</b>.</span>`
                        break
                    case 'pending':
                        text = `<span>Solicitou <b>Revisão</b> da minuta.</span>`
                        break
                    case 'edital':
                        text = `<span>Criou orçamento para <b>Publicação de Edital</b> no valor de: <b>${e.target.value.toLocaleString('pt-BR', currency_br)}</b>.</span>`
                        break
                    case 'visit':
                        text = `<span>Cadastrou nova <b>visita</b>.</span>`
                        break
                    default:
                        text = 'Evento <b>desconhecido</b>'
                        console.log('Evento desconhecido:')
                        console.log(e)
                        break
                }
                itm_comments += `
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

            // Verificar se existe pagamento pendente para carregar com o pedido aberto
            let show_payments = false
            if (intimacao.services.length){
                for (p of intimacao.payments) {
                    if (!p.confirmed) {
                        show_payments = true
                    }
                }
            }
            if (intimacao.s_nopaid) {
                show_payments = true
            }
            let save_function = ''
            // Se tem pagamento pendente | Salvar não faz nada
            if (show_payments) {
                save_function = "alert('Confirmar pagamento')"
            } else {
                // Salvar o protocolo, a não ser que já tenha
                save_function = "save_prot(this)"
                for (s of intimacao.services) {
                    // Tem prot
                    if (s.prot) {
                        matricula = s.mat
                        // Tem Minuta
                        if (s.minuta) {
                            save_function = "save_"
                        } else {
                            save_function = "edit_minuta(this)"
                        }
                    }
                }
            }
            let service_itm_files = ''
            // Incluir conteúdo principal
            about = 'Incluir conteúdo principal'
            itm_info_body.innerHTML = `{% include "itm/info/content.html" %}`

            let itm_info_serv = itm_info_body.querySelector('#itm_info_serv')
            let itm_info_pay = itm_info_body.querySelector('#itm_info_pay')

            // Basic Services
            about = 'Basic Services'
            let services = ['prot']
            for (i of intimacao.pessoas) {
                services.push('dili')
            }
            services.push('decur')

            // Remove if already exists
            about = 'Remove if already exists'
            for (s of intimacao.services) {
                // Prot
                if (s.type == 'prot') {
                    if (services.includes('prot')) {
                        services.splice(services.indexOf('prot'), 1)
                        continue
                    }
                }
                // Dili
                if (s.nature == 'Diligência') {
                    if (services.includes('dili')) {
                        services.splice(services.indexOf('dili'), 1)
                        continue
                    }
                }
                // Decur
                if (s.nature == 'Decurso') {
                    if (services.includes('decur')) {
                        services.splice(services.indexOf('decur'), 1)
                        continue
                    }
                }
            }

            let service_itm_count = 0

            serv_edital = []
            // Loop existent Services
            about = 'Loop existent Services'
            for (s of intimacao.services) {
                let content = ''
                let files = ''
                let value = ''
                let minuta = ''
                let print = ''
                let negativa = true
                let file = ''
                let edital = ''
                let publicar = false
                let public_intimado = true
                let falecido = false



                if (s.files && s.files.length > 0) {
                    s.files.map(f => {
                        file += `
                            <tr>
                                <td>${f.name}</td>
                                <td><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('itm.get_file') }}?id=${f.id}" target="_blank" rel="noopener noreferrer"><i class="fas fa-sm fa-download"></i></a></td>
                            </tr>
                        `
                    })
                    if (s.edital.files && s.edital.files.length) {
                        Object.values(s.edital.files).forEach((e, i) => {
                            file += `
                                <tr>
                                    <td>Edital - ${i + 1}</td>
                                    <td><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('itm.get_file') }}?id=${e}" target="_blank" rel="noopener noreferrer"><i class="fas fa-sm fa-download"></i></a></td>
                                </tr>
                            `
                        })
    
                    }
                    itm_info_body.querySelector('#info_itm_files').insertAdjacentHTML('beforeend', `${file}`)
                }


                if (s.type == 'prot') {
                    if (s.nature == 'Intimação') {
                        value = data['total'].toLocaleString('pt-BR', currency_br)

                        let devedor = ''
                        info_itm_count = 0
                        intimacao.pessoas.forEach(d => {
                            itm_pessoas.push(d)
                            devedor += `
                                <div class="info_itm_endereco row g-2">
                                    <input type="hidden" name="itm_devedor_id_${info_itm_count}" value="${d.id}">
                                    <div class="form-floating col-md-7">
                                        <input ${disabled} type="text" class="form-control" name="itm_devedor_name_${info_itm_count}" value="${d.name}" placeholder="Nome completo" required>
                                        <label for="itm_devedor_name_${info_itm_count}">Nome completo</label>
                                    </div>
                                    <div class="form-floating col-md-2">
                                        <input ${disabled} type="text" class="form-control" maxlength="14" onkeyup="info_itm_mask_cpf(this)" name="itm_devedor_cpf_${info_itm_count}" value="${d.cpf ? mask_cpfcnpj(d.cpf) : ''}"placeholder="000.000.000-00" required>
                                        <label for="itm_devedor_cpf_${info_itm_count}">CPF</label>
                                    </div>
                                    <div class="form-floating col-md-2">
                                        <select ${disabled} id="selection_estcivil" class="form-control" name="itm_devedor_estcivil_${info_itm_count}" required>
                                            <option value=""></option>
                                            ${Object.keys(est_civis).map((e) => {
                                                return `<option value='${e}' ${e === d.estcivil ? "selected" : ''}> ${est_civis[e].name} </option>`
                                            })}
                                        </select>
                                        <label for="itm_devedor_estcivil_${info_itm_count}"> Estado Cívil </label>
                                    </div>
                                    <div class="form-floating col-md-1">
                                        <select ${disabled} id="selection_genero" class="form-control" name="itm_devedor_genero_${info_itm_count}" required>
                                            <option value=""></option>
                                            <option value="f" ${"f" === d.genero ? "selected" : ''}> Fem </option>
                                            <option value="m" ${"m" === d.genero ? "selected" : ''}> Masc </option>
                                        </select>
                                        <label for="itm_devedor_genero_${info_itm_count}"> Gênero </label>
                                    </div>
                                </div>
                            `
                            info_itm_count += 1
                        })

                        // Credor
                        let credor = ''
                            credor += `
                                <div class="form-floating col-md-9">
                                    <input ${disabled} type="text" class="form-control" id="itm_credor_name" ${intimacao.credor ? `name="itm_credor_name" value="${intimacao.credor ? intimacao.credor.name : ''}"` : ''} placeholder="Razão Social" list="credor_name" onchange="select_credor(this)">
                                    <label for="itm_credor_name"> Razão Social do Credor </label>
                                    <datalist id="credor_name">
                                        ${credores.map(c => `<option data-value="${ c['id'] }" value="${ c['name'] }"></option>`).join('')}
                                    </datalist>
                                </div>
                                <div class="form-floating col-md-3">
                                    <input ${disabled} type="text" class="form-control" id="itm_credor_cnpj" ${intimacao.credor ? ` name="itm_credor_cnpj" value="${intimacao.credor ? mask_cpfcnpj(intimacao.credor.cnpj) : ''}" disabled` : ''}  maxlength="18" onkeyup="info_itm_mask_cnpj(this)" placeholder="00.000.000/0000-00" list="credor_cnpj">
                                    <label for="itm_credor_cnpj"> CNPJ </label>
                                    <datalist id="credor_cnpj">
                                        ${credores.map(c => `<option data-value="${ c['id'] }" value="${ c['cnpj'] }"></option>`).join('')}
                                    </datalist>
                                </div>
                                <div class="form-floating col-md-12">
                                    <input ${disabled} type="text" class="form-control" id="itm_credor_end" ${intimacao.credor ? ` name="itm_credor_cnpj" value="${intimacao.credor ? intimacao.credor.sede : ''}" disabled` : ''} placeholder="Endereço completo" list="credor_end">
                                    <label for="itm_credor_end"> Endereço completo da Sede </label>
                                    <datalist id="credor_end">
                                        ${credores.map(c => `<option data-value="${ c['id'] }" value="${ c['sede'] }"></option>`).join('')}
                                    </datalist>
                                </div>
                            <div class="form-floating col-md-12">
                                <textarea ${disabled} class="form-control" name="itm_credor_contr" placeholder="" id="floatingTextarea2" style="height: 78px">${intimacao.contr ? intimacao.contr : ''}</textarea>
                                <label for="floatingTextarea2"> Dados do Contrato ou Escritura originário da dívida na matrícula </label>
                            </div> 
                        `
                        let enderecos = ''
                        info_itm_count = 0
                        Object.values(intimacao.enderecos).forEach(e => {
                            let cep = info_itm_mask_cep('', e.cep)
                            enderecos += `
                                <div class="info_itm_endereco row g-2">
                                    <input ${disabled} hidden type="text" class="form-control" name="itm_end_id_${info_itm_count}" value="${e.id ? e.id : ''}">
                                    <div class="form-floating col-md-6">
                                        <input ${disabled} type="text" class="form-control" name="itm_end_end_${info_itm_count}" value="${e.end ? e.end : ''}"placeholder="Endereço do imóvel" required>
                                        <label for="itm_end_end_${info_itm_count}">Endereço de Intimação</label>
                                    </div>
                                    <div class="form-floating col-md-2">
                                        <input ${disabled} class="form-control form-control-sm" placeholder="Cidade" type="text" list="itm_end_municipio_${info_itm_count}_list" name="itm_end_municipio_${info_itm_count}" value="${e.municipio ? e.municipio : ''}" required/>
                                        <label for="itm_end_municipio_${info_itm_count}">Cidade</label>
                                        <datalist id="itm_end_municipio_${info_itm_count}_list">
                                        </datalist>
                                    </div>
                                    <div class="form-floating col-md-1">
                                        <input ${disabled} type="text" class="form-control minuta_estado" list="itm_end_estado_${info_itm_count}_list" name="itm_end_estado_${info_itm_count}" value="${e.estado ? e.estado : ''}"placeholder="UF" required>
                                        <label for="itm_end_estado_${info_itm_count}">UF</label>
                                        <datalist id="itm_end_estado_${info_itm_count}_list">
                                        </datalist>
                                    </div>
                                    <div class="form-floating col-md-2">
                                        <input ${disabled} type="text" class="form-control" maxlength="10" onkeyup="info_itm_mask_cep(this, '')" name="itm_end_cep_${info_itm_count}" value="${cep}" placeholder="CEP do imóvel" required>
                                        <label for="itm_end_cep_${info_itm_count}">CEP</label>
                                    </div>
                                    <div class="form-floating col-md-1">
                                        ${intimacao.services[0] && !intimacao.services[0].minuta ? `<button tabindex="-1" type="button" class="btn btn-sm ms-2 btn-outline-danger" onclick="del_end_itm_info(event, this, '${e.id}')"><i class="fas fa-sm fa-trash"></i></button>`: ''}
                                    </div>
                                </div>
                            `
                            info_itm_count += 1
                        })

                        content += `{% include "itm/info/form_itm.html" %}`

                        let min_devedor = ''
                        let min_pessoas = []
                        info_itm_count = 0
                        for (m of itm_pessoas) {

                            if(Object.keys(est_civis).includes(m.estcivil)) {
                                m.estcivil = m.genero === 'f' ? est_civis[m.estcivil].text.replace('_', 'a') : est_civis[m.estcivil].text.replace('_', 'o')
                            } else {
                                m.estcivil = 'Estado Cívil'
                            }

                            min_pessoas.push(`
                                    <input type="checkbox" class="btn-check" id="btn-check_name_${info_itm_count}" autocomplete="off">
                                    <label class="btn btn-sm text-danger" for="btn-check_name_${info_itm_count}"><b>${m.name ? m.name : 'Nome Devedor(a)'}</b></label>, inscrito(a) no CPF Nº 
                                    <input type="checkbox" class="btn-check" id="btn-check_cpf_${info_itm_count}" autocomplete="off">
                                    <label class="btn btn-sm text-danger" for="btn-check_cpf_${info_itm_count}"><b>${m.cpf ? mask_cpfcnpj(m.cpf) : 'CPF Devedor(a)'}</b></label>, 
                                    <input type="checkbox" class="btn-check" id="btn-check_estcivil_${info_itm_count}" autocomplete="off">
                                    <label class="btn btn-sm text-danger" for="btn-check_estcivil_${info_itm_count}"><b>${m.estcivil ? m.estcivil : 'Estado Civil'}</b></label>
                                `)
                            info_itm_count += 1
                        }

                        min_devedor += min_pessoas.join(' e ')
                        let min_enderecos = ''

                        Object.values(intimacao.enderecos).forEach((v, id) => {
                        info_itm_count = id
                        min_enderecos += `
                            <input type="checkbox" class="btn-check" id="btn-check_end_end_${info_itm_count}" autocomplete="off">
                            <label class="btn btn-sm text-danger" for="btn-check_end_end_${info_itm_count}">
                                <b>${v.end ? v.end : 'Logradouro do endereço'}, ${v.municipio ? v.municipio : 'Município'}-${v.estado ? v.estado : 'UF'}</b>
                            </label>
                        `})

                        let min_btn = ''
                        // Tem minuta
                        if (s.minuta) {
                            // Não foi Impressa
                            if (!s.minuta_printed) {
                                min_btn += `
                                    <a class="btn btn-sm btn-outline-success" href="{{ url_for('itm.get_file') }}?id=${s.minuta.id}" target="_blank" rel="noopener noreferrer">Minuta <i class="fas fa-sm fa-download"></i></a>
                                    <a class="btn btn-sm btn-outline-primary"type="button" onclick="info_print_minuta(this, '${intimacao.id}')">Impresso <i class="fas fa-sm fa-print"></i></a>
                                `
                            // Foi Impressa
                            } else {
                                min_btn += `
                                    <a class="btn btn-sm btn-outline-success" href="{{ url_for('itm.get_file') }}?id=${s.minuta.id}" target="_blank" rel="noopener noreferrer">Minuta <i class="fas fa-sm fa-download"></i></a>
                                `
                            }
                        // Minuta pendente
                        } else if (s.minuta_pending) {
                            {% if 'itm-sign' in roles %}
                                min_btn += `
                                    <button type="button" onclick="rejec_minuta(this, '${intimacao.id}')" class="btn btn-outline-danger">Rejeitar</button>
                                    <button type="button" onclick="aprov_minuta(this, '${intimacao.id}')" class="btn btn-outline-success">Aprovar</button>
                                `
                            {% endif %}
                        // Para revisar
                        } else {
                            {% if 'itm-sign' in roles %}
                                min_btn += `
                                    <button type="button" class="btn btn-warning" disabled>Em confecção</button>
                                `
                            {% else %}
                                min_btn += `
                                    <button type="button" onclick="revis_minuta(this, '${intimacao.id}')" class="btn btn-outline-success">Solicitar Revisão</button>
                                `
                            {% endif %}
                        }
                        minuta += `{% include "itm/info/min_itm.html" %}`
     
                    }

                    info_itm_count = 0
                    itm_info_serv.insertAdjacentHTML('beforeend',  `
                        <div class="accordion-item accordion-border" value="${s.type}">
                            <h2 class="accordion-header" id="itm_info_accord_h2_${info_itm_count}">
                                <button class="accordion-button text-center collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#itm_info_accord_${info_itm_count}" aria-expanded="false" aria-controls="itm_info_accord_${info_itm_count}">
                                    <h5 class="accordion_title">
                                        <span value="${all_natures['attend'][s.type][s.nature][s.id]}" class="nature"><i class="fas fa-sm fa-home mx-2"></i>${s.nature} | <span value="${s.total}" class="value"><b>${s.total.toLocaleString('pt-BR', currency_br)}</b></span></span>
                                        <span>Código | <b name="cod" value="${s.prot}">${s.prot}</b></span>
                                        ${s.selo ? `<span>Selo | <b name="selo" value="${s.selo}">${s.selo}</b></span>` : ''}
                                        <span>Data | <b>${new Date(s.prot_date * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</b></span>
                                    </h5>
                                </button>
                            </h2>
                            <div id="itm_info_accord_${info_itm_count}" class="accordion-collapse collapse ${intimacao.services[0] && !intimacao.services[0].minuta_printed ? 'show' : ''}" aria-labelledby="itm_info_accord_h2_${info_itm_count}" data-bs-parent="#itm_info_serv">
                                <div class="accordion-body">
                                    <div>
                                        ${content}
                                        ${minuta}
                                       
                                        ${print}
                                        <div id="info_itm_service_edital"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `)
                    info_itm_count += 1

                    // Preencher os estados dos endereços
                    document.querySelectorAll('.minuta_estado').forEach(input => {
                        let select = input.parentElement.querySelector('datalist')
                        select.insertAdjacentHTML('beforeend', estados.sort().map(est => `<option data-value="${ est }" value="${ est }"></option>`).join(''))
                        // Preencher os municipios dos endereços
                        fill_minuta_municipios(input)
                    })
                    
                    let error_fields = result['services'][0].minuta_wrong
                    let checkboxes = document.querySelectorAll('.btn-check')
                    let body_inputs = document.querySelector('#itm_info_minuta')
                    let names = body_inputs.querySelectorAll('.form-control')
                    for(e of error_fields) {
                        {% if 'itm-sign' in roles %}
                            for (c of checkboxes) {
                                let checkbox = c.id
                                if(checkbox.includes(e)) {
                                    c.checked = true
                                }
                            }
                        {% endif %}
                        for(i of names) {
                            let name = i.name
                            if(name.includes(e)) {
                                if(!name.includes('end_end')) {
                                    i.classList.add('border', 'border-danger')
                                    let p = document.createElement('p')
                                    p.innerHTML = 'Incorreto'
                                    i.parentElement.append(p)
                                    p.classList.add('text-danger', 'd-flex')
                                }
                                else {
                                    let end = document.getElementsByName(`itm_end_end_${name.split('_').slice(-1)}`)
                                    for(e of end) {
                                        let div = e.closest('.info_itm_endereco')
                                        let input = div.querySelectorAll('input:not([hidden])')
                                        for(t of input) {
                                            t.classList.add('border', 'border-danger')
                                            let p = document.createElement('p')
                                            p.innerHTML = 'Incorreto'
                                            t.parentElement.append(p)
                                            p.classList.add('text-danger', 'd-flex')
                                        }
                                    }
                                }
                            }
                        }
                    }
        
                } else if (s.type == 'cert') {
                    if (s.nature == 'Diligência') {
                        codigo = `
                            <span name="cod" value="${s.prot}">Código | <b>${s.prot}</b></span>
                        `
                        let cert_minuta = `Referente à Intimação protocolada sob o nº ${intimacao.services[0].prot}, do(a) devedor(a) fiduciante <b>${s.pessoa.name}</b>, portador(a) do CPF nº <b>${mask_cpfcnpj(s.pessoa.cpf)}</b>, `
                        let cert_visits = ''
                        for (p of intimacao.pessoas) {
                            if (p.id === s.pessoa.id) {
                                let dili_visit_map = {}
                                for (v of p.visits) {
                                    if (Object.keys(dili_visit_map).includes(v.end.id)) {
                                        dili_visit_map[v.end.id].push(v)
                                    } else {
                                        dili_visit_map[v.end.id] = [v]
                                    }
                                }
                                for (c of Object.keys(dili_visit_map)) {
                                    for (v of dili_visit_map[c]) {
                                        if (v.result !== 'n' && v.result !== 'd' && v.result !== 'i' && v.result !== 'm') {
                                            negativa = false
                                            public_intimado = true
                                        } else if (v.result === 'f'){
                                            falecido = true
                                        } else {
                                            public_intimado = false
                                        }
                                    }
                                    cert_visits += `
                                        <div style="border-radius:16px; box-shadow:rgba(0, 0, 0, 0.35) 9px 6px 16px; padding: 12px; margin: 16px;">
                                            ${intimacao.enderecos[c].end ? `<h6><b>${intimacao.enderecos[c].end}</b> - ${intimacao.enderecos[c].municipio}/${intimacao.enderecos[c].estado}</h6>` : ''}
                                            <hr class="my-3">
                                            <ul class="list-group list-group-flush">
                                                ${dili_visit_map[c].map(cv => `
                                                        <li class="list-group-item list-group-item-action">
                                                            <div class="item-visita">
                                                                <div class="fw-bold">
                                                                    ${
                                                                        cv.result == 'p' ? '<h5 class="text-success fw-bold">Positiva</h5>' :
                                                                        cv.result == 'n' ? '<h5 class="text-danger fw-bold">Negativa</h5>' :
                                                                        cv.result == 'r' ? '<h5 class="text-primary fw-bold">Recusou</h5>' :
                                                                        cv.result == 'f' ? '<h5 class="fw-bold">Falecido</h5>' :
                                                                        cv.result == 'd' ? '<h5 class="text-warning fw-bold">Outros</h5>' :
                                                                        cv.result == 'i' ? '<h5 class="text-danger fw-bold">Incorreto</h5>' :
                                                                        cv.result == 'm' ? '<h5 class="text-info">Mudou</h5>' :
                                                                        cv.result == 'c' ? '<h5 class="text-secondary">Cartório</h5>' :
                                                                    ''}
                                                                </div>
                                                                <div>
                                                                    <span class="badge bg-primary rounded-pill">${new Date(cv.date * 1000).toLocaleString('default', { timeZone: 'America/Sao_Paulo'})}</span>
                                                                </div>
                                                            </div>
                                                            <div>
                                                                ${cv.comment?`<b>Ocorrência: </b>${cv.comment}`:''}
                                                            </div>
                                                        </li>
                                                    `).join('')
                                                }
                                            </ul>
                                        </div>
                                    `
                                }
                                if (!public_intimado && negativa) {
                                    serv_edital.push(`${p.name}, portador(a) do CPF nº ${mask_cpfcnpj(p.cpf)}, ${p.estcivil}`) 
                                }
                                Object.values(dili_visit_map).forEach((map, i) => {
                                    map.forEach((v, index) => {
                                        if (index === 0) { 
                                            if(i === 0) {
                                                cert_minuta += `conforme endereço indicado: <b>${v.end.end}, ${v.end.municipio}-${v.end.estado}</b>,`
                                            } else {
                                                cert_minuta += `Certifico, ainda, tentativa de intimação no outro endereço indicado: <b>${v.end.end}, ${v.end.municipio}-${v.end.estado}</b>,`
                                            }
                                            if (! v.result.includes('c')) {
                                                if (map.length <= 1) {
                                                    cert_minuta += ` foi realizada diligência no dia `
                                                } else {
                                                    cert_minuta += ` foram realizadas diligências nos dias `
                                                }
                                            }
                                        }
                                        if (! v.result.includes('c')) {
                                            cert_minuta += `<b>${new Date(v.date * 1000).toLocaleString('default', {dateStyle: 'long', timeStyle: 'medium', timeZone: 'America/Sao_Paulo'})}</b>, `
                                        } else {
                                            cert_minuta += `informo que (a) notificando(a) compareceu a este Serviço Registral, no dia <b>${new Date(v.date * 1000).toLocaleString('default', {dateStyle: 'long', timeStyle: 'medium', timeZone: 'America/Sao_Paulo'})}</b>, `
                                        }                                    
                                    });

                                    map.forEach((r, ind) => {
                                        if (r.result.includes('p')) {
                                            cert_minuta += `e <b>FOI INTIMADO</b> pessoalmente de todo o teor da intimação prevista nos §§ 3º e 4º do artigo 26 da Lei 9.514/97, recebeu a contrafé e assinou a via de recebimento${r.comment ? ', ' + r.comment : ''}. `
                                        } else if (r.result.includes('r')) {
                                            cert_minuta += `e <b>FOI INTIMADO(A) PESSOALMENTE</b> de todo o teor da intimação prevista nos §§ 3º e 4º do artigo 26 da Lei 9.514/97, o(a) qual após tomar conhecimento do inteiro teor da notificação <b>recusou-se a assinar</b>. `
                                        } else if (r.result.includes('f')) {
                                            cert_minuta += `e de acordo com informações prestadas pelo(a) Sr(a). ${r.comment}, o(a) destinatário(a) <b>FALECEU</b>. `
                                        } else if (r.result.includes('c')) {
                                            cert_minuta += `tendo sido <b>NOTIFICADO(A) PESSOALMENTE<b> de todo o teor da intimação prevista nos §§ 3º e 4º do artigo 26 da Lei 9.514/97, recebeu a contrafé e assinou a via de recebimento. `
                                        } else {
                                            if (r.result.includes('i')) {
                                                cert_minuta += `e <b>NÃO FOI NOTIFICADO(A)</b>, tendo em vista que o endereço encontra-se incompleto/incorreto, pois faltou constar a informação referente ao ${r.comment ? r.comment : ''}. `
                                            } else if (r.result.includes('d')) {
                                                cert_minuta += `e <b>NÃO FOI NOTIFICADO(A)</b>, tendo em vista que ${r.comment ? r.comment : ''}. `
                                            } else if (r.result.includes('m')) {
                                                cert_minuta += `e <b>NÃO FOI NOTIFICADO(A)</b>, tendo em vista que o(a) notificando(a) MUDOU-SE, ${r.comment ? r.comment : ''}. `
                                            } else {
                                                if(r.result.includes('n') && ind === 2) {
                                                    cert_minuta += `e <b>NÃO FOI NOTIFICADO(A)</b>, tendo em vista a realização de 3 tentativas de intimação e não foi encontrado. `
                                                }
                                            }

                                        }
                                    })
                                }) 
                                if (public_intimado) {
                                    cert_minuta += `CERTIFICO que, em virtude da ocorrência acima, o destinatário foi intimado para purgar a mora em 15 dias. `
                                } else if (falecido){
                                    cert_minuta += `CERTIFICO que, em virtude da ocorrência acima, o(a) destinatário(a) <b>não foi notificado(a)</b>. `
                                } else {
                                    cert_minuta += `CERTIFICO que, em virtude da ocorrência acima, o(a) destinatário(a) não foi notificado(a), que se encontra em local ignorado. Diante do exposto, poderá o credor requerer a publicação de edital para a intimação do(a) devedor(a). `
                                }
                                cert_minuta += `Emitido por ${s.func} - Escrevente.`
                                break
                            }

                        }
                        itm_info_serv.insertAdjacentHTML('beforeend',  `
                            <div class="accordion-item accordion-border" value="cert">
                                <h2 class="accordion-header" id="itm_info_accord_h2_${info_itm_count}">
                                    <button class="accordion-button text-center collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#itm_info_accord_${info_itm_count}" aria-expanded="false" aria-controls="itm_info_accord_${info_itm_count}">
                                        <h6 class="accordion_title">
                                            <span value="${all_natures['attend']['cert']['Diligência']}" class="nature"><i class="fas fa-sm fa-user mx-2"></i>Diligência</span>
                                            <span> ${s.pessoa.name} | <input style="width: 140px;" disabled value="${mask_cpfcnpj(s.pessoa.cpf)}"></input></span>
                                            ${codigo}
                                            <span>Data | <b>${new Date(s.timestamp * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</b></span>
                                            {% if 'itm-sign' in roles %}
                                                <a onclick="undo_dili(this, '${s.id}')" type='button' class='btn btn-sm btn-outline-danger'> <i class='fas fa-sm fa-trash'></i> </a>
                                            {% endif %}
                                        </h6>
                                    </button>
                                </h2>
                                <div id="itm_info_accord_${info_itm_count}" class="accordion-collapse collapse" aria-labelledby="itm_info_accord_h2_${info_itm_count}" data-bs-parent="#itm_info_serv">
                                    <div class="accordion-body">
                                        <div>
                                            <h5>Visitas</h5>
                                            ${cert_visits ? cert_visits : '' }
                                            <h5>Minuta</h5>
                                            <div>
                                                <label for="info_cert_dili_minuta_${info_itm_count}" class="form-label"></label>
                                                <textarea class="form-control" id="info_cert_dili_minuta_${info_itm_count}" rows="12">${cert_minuta}</textarea>
                                            </div>
                                            <a onclick="info_dili_copy_minuta(this, '${info_itm_count}')" class="btn btn-sm btn-outline-success mt-3"><i class="fas fa-sm fa-copy"> Copiar</i></a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                        `)
                        info_itm_count += 1
                        for (p of intimacao.pessoas) {
                            if (s.pessoa.name === p.name) {
                                intimacao.pessoas.splice(intimacao.pessoas.indexOf(p), 1)
                            }
                        }

                    } else if (s.nature == 'Decurso') {
                        let decu_devedor = ''
                        let decu_pessoas = []
                        for (l of itm_pessoas) {
                            let decur_visit_map = {}
                            for (v of l.visits) {
                                if (Object.keys(decur_visit_map).includes(v.end.id)) {
                                    decur_visit_map[v.end.id].push(v)
                                } else {
                                    decur_visit_map[v.end.id] = [v]
                                }
                            }
                            let results = l.visits.map(v => v.result)
                            if (results.includes('p')) {
                                let v = l.visits[results.indexOf('p')]
                                decu_pessoas.push(`<b>${l.name}</b>, portador(a) do CPF nº <b>${mask_cpfcnpj(l.cpf)}</b>, ${l.estcivil}, intimado(a) pessoalmente no dia <b>${new Date(v.date * 1000).toLocaleString('default', {dateStyle: 'long', timeStyle: 'medium', timeZone: 'America/Sao_Paulo'})}, NO ENDEREÇO ${v.end.end}, ${v.end.municipio}-${v.end.estado}</b>`)
                            } else if (results.includes('r')) {
                                let v = l.visits[results.indexOf('r')]
                                decu_pessoas.push(`<b>${l.name}</b>, portador(a) do CPF nº <b>${mask_cpfcnpj(l.cpf)}</b>, ${l.estcivil}, intimado(a) pessoalmente no dia <b>${new Date(v.date * 1000).toLocaleString('default', {dateStyle: 'long', timeStyle: 'medium', timeZone: 'America/Sao_Paulo'})}, NO ENDEREÇO ${v.end.end}, ${v.end.municipio}-${v.end.estado}</b>`)
                            } else if (results.includes('f')) {
                                let v = l.visits[results.indexOf('f')]
                                decu_pessoas.push(`<b>${l.name}</b>, portador(a) do CPF nº <b>${mask_cpfcnpj(l.cpf)}</b>, ${l.estcivil}, no dia ${new Date(v.date * 1000).toLocaleString('default', {dateStyle: 'long', timeStyle: 'medium', timeZone: 'America/Sao_Paulo'})}, NO ENDEREÇO ${v.end.end}, ${v.end.municipio}-${v.end.estado}, de acordo com informações prestadas pelo(a) Sr(a). ${v.comment}, o(a) destinatário(a) <b>FALECEU</b>`)
                            } else if (results.includes('c')) {
                                let v = l.visits[results.indexOf('c')]
                                decu_pessoas.push(`<b>${l.name}</b>, portador(a) do CPF nº <b>${mask_cpfcnpj(l.cpf)}</b>, ${l.estcivil}, no dia <b>${new Date(v.date * 1000).toLocaleString('default', {dateStyle: 'long', timeStyle: 'medium', timeZone: 'America/Sao_Paulo'})}</b>, <b>FOI NOTIFICADO(A) PESSOALMENTE NO CARTÓRIO</b>`)
                            } else { 
                                for (c of Object.keys(decur_visit_map)) {
                                    for (v of decur_visit_map[c]) {
                                        if (v.result !== 'n' && v.result !== 'd' && v.result !== 'i' && v.result !== 'm') {
                                            negativa = false
                                            public_intimado = true
                                        } else {
                                            public_intimado = false
                                        }
                                    }
                                }
                                if (!public_intimado && negativa) {
                                    decu_pessoas.push(`<b>${l.name}</b>, portador(a) do CPF nº <b>${mask_cpfcnpj(l.cpf)}</b>, ${l.estcivil}, intimado(a) via edital por 03 dias consecutivos, nos dias <b>${new Date(intimacao.services[0].edital.dia1).toLocaleString('default', { dateStyle: 'short', timeZone: 'UTC' })}</b>, <b>${new Date(intimacao.services[0].edital.dia2).toLocaleString('default', { dateStyle: 'short', timeZone: 'UTC' })}</b>, <b>${new Date(intimacao.services[0].edital.dia3).toLocaleString('default', { dateStyle: 'short', timeZone: 'UTC' })}</b>`)
                                }
                            }
                        }
                        decu_devedor += decu_pessoas.join(' e ')
                        let cert_minuta = `A pedido da parte interessada e para os fins que dispõe o art. 26 § 7º da Lei 9.514/97, certifica que <b>não foi efetuado pelo(a) devedor(a)(s) nesta Serventia a purga das prestações vencidas e as que viessem a vencer até a data do pagamento,</b> juntamente, com os juros convencionados e as custas de intimação. ${itm_pessoas.length >= 1 ? 'Devedor(a)' : 'Devedores' }: ${decu_devedor}, ${itm_pessoas.length >= 1 ? 'signatário(a)' : 'signatário(a)s' } de ${result.contr}, registrado sob a matrícula nº ${result.services[0].mat}, desta Serventia; referente ao imóvel situado no: ${Object.values(result.enderecos)[0].end}, ${Object.values(result.enderecos)[0].municipio}-${Object.values(result.enderecos)[0].estado}.`

                        itm_info_serv.insertAdjacentHTML('beforeend',  `
                            <div class="accordion-item accordion-border" value="cert">
                                <h2 class="accordion-header" id="itm_info_accord_h2_${info_itm_count}">
                                    <button class="accordion-button text-center collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#itm_info_accord_${info_itm_count}" aria-expanded="false" aria-controls="itm_info_accord_${info_itm_count}">
                                        <h6 class="accordion_title">
                                            <span value="${all_natures['attend']['cert']['Decurso']}" class="nature"><i class="fas fa-sm fa-user mx-2"></i>Decurso</span>
                                            <span name="cod" value="${s.prot}">Código | <b>${s.prot}</b></span>
                                            <span>Data | <b>${new Date(s.timestamp * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</b></span>
                                        </h6>
                                    </button>
                                </h2>
                                <div id="itm_info_accord_${info_itm_count}" class="accordion-collapse collapse" aria-labelledby="itm_info_accord_h2_${info_itm_count}" data-bs-parent="#itm_info_serv">
                                    <div class="accordion-body">
                                        <div>

                                            <h5>Minuta</h5>
                                            <div>
                                                <label for="info_cert_decur_minuta" class="form-label"></label>
                                                <textarea class="form-control" id="info_cert_decur_minuta" rows="12">${cert_minuta}</textarea>
                                            </div>
                                            <a onclick="info_decur_copy_minuta(this)" class="btn btn-sm btn-outline-success mt-3"><i class="fas fa-sm fa-copy"> Copiar</i></a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                        `)
                    }
                } else {
                    continue
                }

                service_itm_count += 1
            }
            if(serv_edital.length) {
                let edital_minuta = `Márcio Silva Fernandes, Oficial Registrador do Cartório de Registro de Imóveis de Cidade Ocidental-GO, em ${new Date().toLocaleString('default', {dateStyle: 'long', timeZone: 'America/Sao_Paulo'})}, segundo as atribuições conferidas pelo art. 26, § 4º, da Lei nº 9.514, de 20 de novembro 1997, depois de frustrada a intimação do(a) devedor(a) fiduciário no endereço informado pelo credor, científica a todos os que o virem que, pelo presente edital, FICA INTIMADO(A): ${serv_edital.join(` e `)}, relativas ao ${result.contr}, que tem como objeto o imóvel situado no: ${Object.values(result.enderecos)[0].end}, ${Object.values(result.enderecos)[0].municipio}-${Object.values(result.enderecos)[0].estado}, registrado sob a matrícula nº ${result.services[0].mat} a comparecer a este Serviço de registro de Imóveis, situado na: SQ 12, Quadra 11, Lote 56, Edifício Santiago, Centro, Cidade Ocidental-GO, para satisfazer as prestações vencidas e as que vierem a vencer até a data do pagamento, juntamente com os juros convencionados e as custas de intimação. O comparecimento deverá ocorrer no prazo de 15 (quinze) dias, a contar da data da última publicação do presente edital. Fica ainda cientificada que o não cumprimento da referida obrigação no prazo estipulado garante o direito de consolidação da propriedade do imóvel em face do(a) credor(a) - ${intimacao.credor.name}, inscrito(a) no CNPJ/MF sob nº ${mask_cpfcnpj(intimacao.credor.cnpj)}, nos termos do art. 26, § 7°, da Lei nº 9.514/97. E para que chegue ao conhecimento dos interessados, foi publicado o presente edital, na forma da Lei. Selo nº: ${result.services[0].edital.selo} consulte este selo em: https://see.tjgo.jus.br.` 
                let edital = `
                    <div>
                        <h5>Minuta</h5>
                        <div>
                            <label for="info_edital_minuta" class="form-label"></label>
                            <textarea class="form-control" id="info_edital_minuta" rows="16">${edital_minuta}</textarea>
                        </div>
                        <a onclick="info_edital_copy_minuta(this)" class="btn btn-sm btn-outline-success mt-3"><i class="fas fa-sm fa-copy"> Copiar</i></a>
                    </div>
                `
                let info_itm_service_edital = itm_info_body.querySelector('#itm_info_serv')
                info_itm_service_edital.insertAdjacentHTML('beforeend', `{% include "itm/info/min_edital.html" %}`)
            }
            // Pending Prot
            about = 'Pending Prot'
            if (services.includes('prot')) {
                let data_atual = (new Date(Date.now() - (new Date()).getTimezoneOffset() * 60000)).toISOString().slice(0, 10)
                services.splice(services.indexOf('prot'), 1)
                itm_info_serv.insertAdjacentHTML('beforeend', `
                    
                    <div class="accordion-item accordion-border" value="prot">
                        <h2 class="accordion-header" id="itm_info_accord_h2_${info_itm_count}">
                            <button class="accordion-button text-center collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#itm_info_accord_${info_itm_count}" aria-expanded="false" aria-controls="itm_info_accord_${info_itm_count}">
                                <h5 class="accordion_title">
                                    <span value="${all_natures.ri.prot['Intimação'].id}" class="nature">
                                        <i class="fas fa-sm fa-home"></i> Intimação | <span value="${data['total_prot']}" class="value"><b>${data['total_prot'].toLocaleString('pt-BR', currency_br)}</b></span>
                                    </span>
                                </h5>
                            </button>
                        </h2>
                        <div id="itm_info_accord_${info_itm_count}" class="accordion-collapse collapse show" aria-labelledby="itm_info_accord_h2_${info_itm_count}" data-bs-parent="#itm_info_serv">
                            <div class="accordion-body">
                                <div class="d-flex justify-content-around align-items-center">
                                    <span>
                                        Código <br>
                                        <input style="max-width: 80px; text-align: center;" name="cod" placeholder="Protocolo" maxlength="6" ${ saldo >= data['total_prenot'] ? '' : 'disabled'} type="text">
                                    </span>
                                    <span>
                                        Data <br>
                                        <input class="col m-2" name="date" value="${data_atual}" placeholder="" ${ saldo >= data['total_prenot'] ? '' : 'disabled'} type="date">
                                    </span>
                                    <span>
                                        Selo <br>
                                        <input style="min-width: 230px; text-align: center;" name="selo" placeholder="Prenotação" onkeyup="check_selo_itm(this)" maxlength="24" ${ saldo >= data['total_prenot'] ? '' : 'disabled'} type="text">
                                    </span>
                                    ${! intimacao.mat ? `
                                        <span>
                                            Matrícula <br>
                                            <input style="max-width: 80px; text-align: center;" name="mat" placeholder="Matrícula" maxlength="5" ${ saldo >= data['total_prenot'] ? '' : 'disabled'} type="text">
                                        </span>
                                    ` : '' }
                                </div>

                            </div>
                        </div>
                    </div>
                `)
                info_itm_count += 1
            }

            if (services.includes('dili')) {
                decurso = false
            } else {
                decurso = true
            }

            // (intimacao)

            // Pending Dili
            about = 'Pending Dili'
            externo = false
            while (services.includes('dili')) {
                let content = ''
                let value = data['prot_values']['cert'].toLocaleString('pt-BR', currency_br)
                let visits = ''
                let visits_list = ''
                let end_options = ''
                let people = ''
                let codigo = ''
                let files = ''
                let save_cert_btn = ''
                let credito = saldo >= data['prot_values']['cert']
                let intimado = false
                let visitado = false
                let publicado = false
                let edital = ''
                let enderecos = Object.keys(intimacao.enderecos)
                let results = []
                let visit_map = {}                           
                
                // Minuta Printed
                if (intimacao.services && intimacao.services[0] && intimacao.services[0].minuta_printed ) {
                    
                    // Criar mapa de visitas
                    for (e of Object.keys(intimacao.enderecos)) {
                        visit_map[e] = []
                    }
                    for (v of intimacao.pessoas[0]['visits']) {
                        visit_map[v.end.id].push(v)
                    }
                    if (intimacao.pessoas[0]['intimado']) {
                        intimado = true
                    } else {
                        // Resultados de visitas do devedor
                        for (r of intimacao.pessoas[0]['visits']) {
                            results.push(r['result'])
                        }
                        if (results.includes('p') || results.includes('r') || results.includes('f') || results.includes('c')) {
                            intimado = true
                        } else {
                            for (e of Object.keys(visit_map)) {
                                let e_results = []

                                for (v of visit_map[e]) {
                                    e_results.push(v.result)
                                }
                                if (e_results.includes('m') || e_results.includes('d') || e_results.includes('i')) {
                                    enderecos.splice(enderecos.indexOf(e), 1)
                                } else if (visit_map[e].length === 3) {
                                    enderecos.splice(enderecos.indexOf(e), 1)
                                }
                            }
                            if (enderecos.length == 0) {
                                intimado = true
                            }
                        }
                    }

                    if (! intimado) {
                        for (e of enderecos) {
                            // if (intimacao.enderecos[e].estado !== "{{ config['SERVENTIA']['LOCAL'][0] }}" || intimacao.enderecos[e].municipio !== "{{ config['SERVENTIA']['LOCAL'][1] }}") {
                            //     externo = true
                            // } else {
                                end_options += `
                                    <option value="${intimacao.enderecos[e].id}">${intimacao.enderecos[e].end} - ${intimacao.enderecos[e].municipio}/${intimacao.enderecos[e].estado}</option>
                                `
                            // }
                        }
                    }
                    let end_visit = ''
                    if (end_options) {
                        end_visit += `
                            <div class="form-floating col-md-12">
                                <select class="form-select" name="end_visit">
                                    <option value="" selected>Selecionar endereço de visita</option>
                                    ${end_options}
                                </select>
                                <label for="cur_attend_cred">Endereço de visita selecionado</label>
                            </div>
                        `
                    } else {
                        intimado = true
                    }
                    if (! intimado) {
                        visits += `
                            <h4 class="my-4"><b class="my-3">Informar Visita</b></h4>
                            <div class="row g-1">
                                <div style="margin: 0 auto;" class="col-md-8">
                                    <div class="btn-group btn-group-sm flex-wrap" role="group">
                                        <input type="radio" value="p" class="btn-check" name="result_${service_itm_count}" id="info_itm_positiva_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-success" for="info_itm_positiva_${service_itm_count}">Positiva</label>
                                        <input type="radio" value="n" class="btn-check" name="result_${service_itm_count}" id="info_itm_negativa_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-danger" for="info_itm_negativa_${service_itm_count}">Negativa</label>
                                        <input type="radio" value="r" class="btn-check" name="result_${service_itm_count}" id="info_itm_recusou_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-primary" for="info_itm_recusou_${service_itm_count}">Recusou</label>
                                        <input type="radio" value="f" class="btn-check" name="result_${service_itm_count}" id="info_itm_falecido_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-dark" for="info_itm_falecido_${service_itm_count}">Falecido</label>

                                        <input type="radio" value="d" class="btn-check" name="result_${service_itm_count}" id="info_itm_outros_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-warning" for="info_itm_outros_${service_itm_count}">Outros</label>
                                        <input type="radio" value="i" class="btn-check" name="result_${service_itm_count}" id="info_itm_incorreto_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-danger" for="info_itm_incorreto_${service_itm_count}">Incorreto</label>
                                        <input type="radio" value="m" class="btn-check" name="result_${service_itm_count}" id="info_itm_mudou_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-info" for="info_itm_mudou_${service_itm_count}">Mudou</label>
                                        <input type="radio" value="c" class="btn-check" name="result_${service_itm_count}" id="info_itm_cart_${service_itm_count}" autocomplete="off">
                                        <label class="btn btn-sm btn-outline-secondary" for="info_itm_cart_${service_itm_count}">Cartorio</label>
                                    </div>
                                </div>
                                ${end_visit}
                                <div style="width: 160px;">
                                    <div class="form-floating">
                                        <input type="date" class="form-control" id="info_itm_dia_${service_itm_count}" name="dia" placeholder="">
                                        <label for="info_itm_dia_${service_itm_count}">Data</label>
                                    </div>
                                </div>
                                <div style="width: 120px;">
                                    <div class="form-floating">
                                        <input type="time" class="form-control" id="info_itm_time_${service_itm_count}" name="hora" placeholder="">
                                        <label for="info_itm_time_${service_itm_count}">Hora</label>
                                    </div>
                                </div>
                                <div class="col-md">
                                    <div class="form-floating">
                                        <textarea class="form-control" placeholder="" id="info_itm_comment_${service_itm_count}" name="comment"></textarea>
                                        <label for="info_itm_comment_${service_itm_count}">Ocorrência</label>
                                    </div>
                                </div>
                            </div>
                        `
                    }
                    // Show  Visitas
                    if (intimacao.pessoas[0].visits && intimacao.pessoas[0].visits.length > 0 ) {
                        visits_list += `
                            <hr>
                            <h4 class="my-4">Visitas</h4>
                        `
                        for (v of Object.keys(visit_map)) {
                            
                            if (visit_map[v].length == 0) {
                                continue
                            }
                            visits_list += `
                                <div style="border-radius:16px; box-shadow:rgba(0, 0, 0, 0.35) 9px 6px 16px; padding: 12px; margin: 16px;">
                                    ${intimacao.enderecos[v].end ? `<h6><b>${intimacao.enderecos[v].end}</b> - ${intimacao.enderecos[v].municipio}/${intimacao.enderecos[v].estado}</h6>` : ''}
                                    <hr class="my-3">
                                    <ul class="list-group list-group-flush">
                                        ${visit_map[v].map(c => `
                                                <li class="list-group-item list-group-item-action">
                                                    <div class="item-visita">
                                                        <div class="fw-bold">
                                                            ${
                                                                c.result == 'p' ? '<h5 class="text-success fw-bold">Positiva</h5>' :
                                                                c.result == 'n' ? '<h5 class="text-danger fw-bold">Negativa</h5>' :
                                                                c.result == 'r' ? '<h5 class="text-primary fw-bold">Recusou</h5>' :
                                                                c.result == 'f' ? '<h5 class="fw-bold">Falecido</h5>' :
                                                                c.result == 'd' ? '<h5 class="text-warning fw-bold">Outros</h5>' :
                                                                c.result == 'i' ? '<h5 class="text-danger fw-bold">Incorreto</h5>' :
                                                                c.result == 'm' ? '<h5 class="text-info">Mudou</h5>' :
                                                                c.result == 'c' ? '<h5 class="text-secondary">Cartório</h5>' :
                                                            ''}
                                                        </div>
                                                        <div>
                                                            <span class="badge bg-primary rounded-pill">${new Date(c.date * 1000).toLocaleString('default', { timeZone: 'America/Sao_Paulo'})}</span>
                                                        </div>
                                                        <div>
                                                            <button onclick="delete_visit(this,'${c.id}', '${intimacao.pessoas[0].id}')" type='button' class='btn btn-sm btn-outline-danger'> <i class='fas fa-sm fa-trash'></i></button> 
                                                        </div>
                                                    </div>
                                                    <div>
                                                        ${c.comment?`<b>Ocorrência: </b>${c.comment}`:''}
                                                    </div>
                                                </li>
                                            `).join('')
                                        }
                                    </ul>
                                </div>
                            `
                        }
                    }
                    let save_dili = ''

                    if (intimado && credito && !publicado) {
                        save_dili = 'save_cert'
                        codigo += `
                            <b>Pedido de Certidão</b> | <input  style="width: 180px" class="prot" name="cod" placeholder="Código de atendimento" maxlength="17" ${ saldo >= data['prot_values']['cert'] ? '' : 'disabled'} type="text">
                        `
                        if (intimacao.services.length) {
                            files += `
                                <table class="table table-sm table-hover table-responsive">
                                    <thead>
                                        <tr>
                                            <th scope="col"><b>Carregar arquivo</b></th>
                                            <th scope="col">
                                                <input tabindex="0" onchange="upload_itm_info(this, '${service_itm_count}')" type="file" id="itm_file_${service_itm_count}" multiple name="itm_file_${service_itm_count}" accept=".jpg,.jpeg,.png,.gif,.pdf,.p7s" style="display: none;">
                                                <label class="btn btn-sm btn-outline-primary" for="itm_file_${service_itm_count}">
                                                    <i class="fas fa-sm fa-upload"></i>
                                                </label>
                                            </th>
                                        </tr>
                                    </thead>
                                </table>
                                <ol class="list-group list-group-numbered" id="itm_add_file_${service_itm_count}"></ol>
                            `
                        }
                    } else {
                        save_dili = 'save_visit'
                    }
                    save_cert_btn += `
                        <div class="col-md-12 d-flex justify-content-center align-items-center">
                            <button tabindex="-1" type="button" class="btn mt-3 btn-sm btn-outline-success itm_info_btn_save" onclick="${save_dili}(this, '${intimacao.pessoas[0].id}', '${service_itm_count}')"><i class="fas fa-sm fa-save"></i></button>
                        </div>
                    `
                }

                itm_info_serv.insertAdjacentHTML('beforeend',  `{% include 'itm/info/min_dili.html' %}`)
                info_itm_count += 1
                service_itm_count += 1

                services.splice(services.indexOf('dili'), 1)
                intimacao.pessoas.splice(0, 1)
            }

            // Pending Decur
            about = 'Pending Decur'
            if (services.includes('decur')) {
                let codigo = ''
                let files = ''
                if (decurso && intimacao.s_nodecu) {
                    codigo += `
                        <span><b>Pedido de Certidão </b> | <input style="width: 180px" class="prot" placeholder="Código de atendimento" name="cod" maxlength="17" ${ saldo >= data['prot_values']['cert'] ? '' : 'disabled'} type="text"></span>
                        <button type="button" class="btn btn-sm btn-outline-success mx-4" onclick="save_decur(this, '${intimacao.id}')"><i class="fas fa-sm fa-save"></i></button>
                    `
                    // files += `
                    //     <table class="table table-sm table-hover table-responsive">
                    //         <thead>
                    //             <tr>
                    //                 <th scope="col"><b>Carregar arquivo</b></th>
                    //                 <th scope="col">
                    //                     <input tabindex="0" onchange="upload_itm_info(this, '${service_itm_count}')" type="file" id="itm_file_${service_itm_count}" multiple name="itm_file_${service_itm_count}" accept=".jpg,.jpeg,.png,.gif,.pdf,.p7s" style="display: none;">
                    //                     <label class="btn btn-sm btn-outline-primary" for="itm_file_${service_itm_count}">
                    //                         <i class="fas fa-sm fa-upload"></i>
                    //                     </label>
                    //                 </th>
                    //             </tr>
                    //         </thead>
                    //     </table>
                    //     <ol class="list-group list-group-numbered" id="itm_add_file_${service_itm_count}"></ol>
                        
                    // `
                }



                services.splice(services.indexOf('decur'), 1)
                itm_info_serv.insertAdjacentHTML('beforeend', `
                    <div class="accordion-item accordion-border" value="cert">
                        <h2 class="accordion-header" id="itm_info_accord_h2_${info_itm_count}">
                            <button class="accordion-button text-center collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#itm_info_accord_${info_itm_count}" aria-expanded="false" aria-controls="itm_info_accord_${info_itm_count}">
                                <h5 class="accordion_title">
                                    <span value="${all_natures['attend']['cert']['Decurso']}" class="nature"><i class="fas fa-sm fa-home mx-2"></i>Decurso</span>
                                </h5>
                            </button>
                        </h2>
                        <div id="itm_info_accord_${info_itm_count}" class="accordion-collapse collapse ${intimacao.s_nodecu ? 'show' : ''}" aria-labelledby="itm_info_accord_h2_${info_itm_count}" data-bs-parent="#itm_info_serv">
                            <div class="accordion-body">
                            ${codigo}

                            </div>
                        </div>
                    </div>
                `)
                info_itm_count += 1
                service_itm_count += 1
            }

 
            // Payments
            about = 'Payments'

            // itm_info_pay.innerHTML = result['payments'].map(p => `
            //     <tr>
            //         <td><i class="fas fa-chevron-circle-up"></i></i></td>
            //         <td>${p['confirmed'] ? `<i class="fas fa-sm fa-check"></i>` : `<button tabindex="-1" type="button" class="btn btn-sm ms-2 btn-outline-success" onclick="confirm_pay_itm(this, '${p['id']}')"><i class="fas fa-sm fa-dollar-sign"></i></button>`}</td>
            //         <td>${new Date(p['timestamp'] * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</td>
            //         <td>${p['value'].toLocaleString('pt-BR', currency_br)}</td>
            //     </tr>
            // `).join('')
            let itm_info_pay_list = [].concat(result['payments'], result['services'])
                                        .sort((a, b) => a.timestamp - b.timestamp)

            itm_info_pay.insertAdjacentHTML('beforeend', 
                itm_render_payments(itm_info_pay_list)
            )
            if (! intimacao.services.length) {
                itm_info_body.querySelector('#info_itm_files').insertAdjacentHTML('beforeend', result['files'].map( f => `
                    <tr>
                        <td>${f.name}</td>
                        <td><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('itm.get_file') }}?id=${f.id}" target="_blank" rel="noopener noreferrer"><i class="fas fa-sm fa-download"></i></a></td>
                    </tr>
                ` ).join(''))
            }


                // <td><a class="btn btn-sm btn-outline-success" onclick="sign_file(this, '${f.id}')"><i class="fas fa-sm fa-file-signature"></i></a></td>
            // let file = info_itm.querySelector('#itm_add_file')
            // file.addEventListener('change', (event) => {
            //     const files = event.target.files
            //     let filename = info_itm.querySelector('#itm_add_file_list')
            //     filename.innerHTML = ''
            //     for (const file of files) {
            //       const li = document.createElement('li');
            //       li.textContent = file.name;
            //       li.className = 'list-group-item list-group-item-action'
            //       filename.appendChild(li)
            //     }

            // })
        } else {
            data['error'] ? alert(data['error']) : console.log('Unknown data:', data)
        }

    }).catch(error => { alert(`{{ _('Error in API') }} GET ${api_url} | ${about} ${error}`) }) 
}

function new_edital_file_info_preview(event) {
    const files = event.target.files
    let filename = itm_info_body.querySelector('#edital_file_info_list')
    filename.innerHTML = ''
    for (const file of files) {
        const li = document.createElement('li');
        li.textContent = file.name;
        li.className = 'list-group-item list-group-item-action'
        filename.appendChild(li)
    }
}  

function select_credor(that) {
    let parent_e = that.parentElement.parentElement
    let cnpj = parent_e.querySelector('#itm_credor_cnpj')
    let end = parent_e.querySelector('#itm_credor_end')

    let selected = that.list.querySelector(`option[value="${that.value}"]`)
    if (selected) {
        cnpj.value = cnpj.list.querySelector(`option[data-value="${selected.dataset.value}"]`).value
        cnpj.disabled = true
        end.value = end.list.querySelector(`option[data-value="${selected.dataset.value}"]`).value
        end.disabled = true
    } else {
        cnpj.value = ''
        cnpj.disabled = false
        end.value = ''
        end.disabled = false
    }
}

const info_itm_mask_cpf = async function (that) {
    let cpf = await mask_cpfcnpj(that.value)
    that.value = cpf
    cpf=cpf.replace(/\D/g,"")
    if (cpf.length == 11) {
        if (! await check_cpfcnpj(cpf)) {
            that.value = that.value.slice(0, -1)
            alert("CPF inválido")
        }
    }
}

const info_itm_mask_cnpj = async function (that) {
    let cnpj = await mask_cpfcnpj(that.value)
    that.value = cnpj
    cnpj=cnpj.replace(/\D/g,"")

    if (cnpj.length == 14) {
        if (!check_cpfcnpj(cnpj)) {
            that.value = that.value.slice(0, -1)
            alert("CNPJ inválido")
        }
    } 
}

const info_itm_mask_cep = function (that, cep_api) {
    if (that.value) {
        cep=that.value.replace(/\D/g,"")
        cep=cep.replace(/^(\d{2})(\d)/,"$1.$2")
        cep=cep.replace(/\.(\d{3})(\d)/,".$1-$2")
        that.value = cep
    } else {
        if(cep_api) {
            cep=cep_api.replace(/\D/g,"")
            cep=cep.replace(/^(\d{2})(\d)/,"$1.$2")
            cep=cep.replace(/\.(\d{3})(\d)/,".$1-$2")
            return cep
        }

    }
}

const check_selo_itm = function (that) {
    if (that.value) {
        that.value=that.value.replace(/\D/g,"")
    }
}

const add_end_itm_info = (that) => {
    that.previousElementSibling.insertAdjacentHTML("beforeend", `
        <div class="info_itm_endereco row g-2">
            <div class="form-floating col-md-6">
                <input type="text" class="form-control" name="itm_end_end_${info_itm_count}" value=""placeholder="Logradoudo do novo endereço de intimação" required>
                <label for="itm_end_end_${info_itm_count}">Novo Endereço de Intimação</label>
            </div>
            <div class="form-floating col-md-2">
                <input type="text" class="form-control" name="itm_end_municipio_${info_itm_count}" value="" placeholder="Cidade" required>
                <label for="itm_end_municipio_${info_itm_count}">Cidade</label>
            </div>
            <div class="form-floating col-md-1">
                <input maxlength="2" type="text" class="form-control" name="itm_end_estado_${info_itm_count}" value="" placeholder="UF" required>
                <label for="itm_end_estado_${info_itm_count}">UF</label>
            </div>
            <div class="form-floating col-md-2">
                <input type="text" class="form-control" maxlength="10" onkeyup="info_itm_mask_cep(this, '')" name="itm_end_cep_${info_itm_count}" value="" placeholder="CEP do imóvel" required>
                <label for="itm_end_cep_${info_itm_count}">CEP</label>
            </div>
            <div class="form-floating col-md-1">
            </div>
        </div>
    `)
    info_itm_count += 1
}

function del_end_itm_info(event, that, id){
    if (confirm('Deseja realmente DELETAR o endereço')) {
        event.stopPropagation()
        data = {
            'id': intimacao.id,
            'end':id,
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.del_end') }}`
        fetch(api_url, {method: 'DELETE',
                        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                        body: JSON.stringify( data ) })
        .then(response => response.json()).then(data => {
            if (data['result']) {
                that.closest('.info_itm_endereco').remove()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                    that.innerHTML = btn_html }
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html})
    }
}



function orc_edital_itm_info(that){
    if (confirm('Deseja realmente solicitar ORÇAMENTO do edital')) {
        to_send = {
            'id': intimacao.id,
            'action': 'edital',
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.put_itm') }}`
        fetch(api_url, {method: 'PUT',
                        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                        body: JSON.stringify( to_send ) })
        .then(response => response.json()).then(data => {
            if (data['result']) {
                open_itm_info(intimacao.id)
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                    that.innerHTML = btn_html }
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html})
    }
}


function upload_itm_dili(that, count) {
    let oparent = that.closest('.row')
    files.innerHTML = ''

    let files = oparent.querySelector(`#itm_info_add_file_${count}`)
    for (const sfile of files) {
        const li = document.createElement('li');
        li.textContent = sfile.name;
        li.className = 'list-group-item list-group-item-action'
        files.appendChild(li)
    }





    // let file = oparent.querySelector(`#itm_file_${ind}`) 

    // if (!file.value.length) {
    //     alert('Selecione os arquivos')
    //     return
    // }
    // // Para cada arquivo do input criar um item na lista uploads
    // uploads = []
    // for (var i = 0; i < file.files.length; i++) {
    //     let reader = new FileReader()
    //     reader.fileName = file.files[i].name
    //     reader.fileType = file.files[i].type
    //     reader.fileIndex = i
    //     reader.readAsDataURL(file.files[i])
    //     reader.onload = () => {
    //         reader['data'] = reader.result
    //             .replace('data:', '')
    //             .replace(/^.+,/, '')
    //     }
    //     uploads.push(reader)
    // }
    // const load_files = await loop_files(uploads)
}

function info_dili_copy_minuta(that, count) {

    let parent_e = that.parentElement
    let text_minuta = parent_e.querySelector(`#info_cert_dili_minuta_${count}`)
    text_minuta.setSelectionRange(0, text_minuta.value.length);
    navigator.clipboard.writeText(text_minuta.value)
        .then()
        .catch((error) => {
            console.error('Erro ao copiar o texto:', error);
        });
}

function info_decur_copy_minuta(that) {

    let parent_e = that.parentElement
    let text_minuta = parent_e.querySelector(`#info_cert_decur_minuta`)
    text_minuta.setSelectionRange(0, text_minuta.value.length);
    navigator.clipboard.writeText(text_minuta.value)
        .then()
        .catch((error) => {
            console.error('Erro ao copiar o texto:', error);
        });
}


function info_edital_copy_minuta(that) {

    let parent_e = that.parentElement
    let text_minuta = parent_e.querySelector(`#info_edital_minuta`)
    text_minuta.setSelectionRange(0, text_minuta.value.length);
    navigator.clipboard.writeText(text_minuta.value)
        .then()
        .catch((error) => {
            console.error('Erro ao copiar o texto:', error);
        });
}

function upload_dili_file_list(that) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let itm_file = $('itm_info_file')

    itm_file.insertAdjacentHTML('beforeend', `
        <tr  class="itm_file">
            <td></td>
            <td>name</td>
            <td><button tabindex="-1" type="button" class="btn btn-sm btn-outline-danger" onclick="this.closest('.itm_file').remove()"><i class="fas fa-sm fa-trash"></i></button></td>
        </tr>
    `)
    that.innerHTML = btn_html
}

function upload_itm_info(that, id) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let itm_file = $(`itm_add_file_${id}`)
    let items = ''
    for (f of that.files) { items += `
        <li>
            <b>${f.name}</b>
            <button tabindex="-1" type="button" class="mx-4 btn btn-sm btn-outline-danger" onclick="this.closest('li').remove()"><i class="fas fa-sm fa-trash"></i></button>
        </li>`
    }
    itm_file.insertAdjacentHTML('beforeend',  items)
    that.innerHTML = btn_html
}

function upload_itm_file_info(that, id) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let itm_file = $(`itm_info_add_file_${id}`)
    let items = ''
    for (f of that.files) { items += `
        <li>
            <b>${f.name}</b>
            <button tabindex="-1" type="button" class="btn btn-sm btn-outline-danger" onclick="this.closest('li').remove()"><i class="fas fa-sm fa-trash"></i></button>
        </li>`
    }
    itm_file.insertAdjacentHTML('beforeend',  items)
    that.innerHTML = btn_html
}

var save_comment = async function(that) {
    // let btn_start = info_itm.querySelector('.startRazed')
    // let btn_html = btn_start.innerHTML
    // btn_start.innerHTML = spinner_w
    if (confirm('Deseja realmente SALVAR as alterações?')) {
        // Comment
        let comment = info_itm.querySelector('#itm_info_comment').value

        to_send = {
            'id': that.name,
            'files': uploads,
            'services': [],
            'pessoas': [],
            'comment': comment ? comment.trim() : '',
        }
        // Services
        let cpf_list = []
        let service_list = $('itm_info_serv').children
        for (let i = 0; i < service_list.length; i++) {
            let stype = service_list[i].attributes.value.value
            let prot = service_list[i].querySelector('input[name="cod"]')

            let nature = service_list[i].querySelector('span.nature').attributes.value.value

            // for (const service of itm_data.services) {
            if (!Object.values(all_natures['attend'][stype]).includes(nature)) {
                alert(`Natureza do serviço ${prot} inválida save_comment`)
            return
            }
            // }
            // let value = service_list[i].querySelector('span.value').attributes.value.value

            switch (stype) {
                case 'prot':
                    if (nature == all_natures['attend']['prot']['Intimação']['id']) {
                        // Se tem input
                        if (prot) {
                            let selo = service_list[i].querySelector('input[name="selo"]').value
                            let prot_date = service_list[i].querySelector('input[name="date"]').value
                            // Se foi digitado o prot
                            if (! prot.value.trim()) {
                                alert('Digite o Protocolo.')
                                return
                            }
                            prot = prot.value.trim().toUpperCase()
                            // Validar
                            if (! prot.length === 5 || ! prot.length === 6) {
                                alert('Protocolo inválido.')
                                return
                            }
                            let service = {
                                'type': stype,
                                'prot': prot,
                                'prot_date': prot_date,
                                'selo': selo,
                                'nature': nature,
                            }
                            let mat = service_list[i].querySelector('input[name="mat"]')
                            if (mat) {
                                service['mat'] = mat.value
                            }
                            // Gravar
                            to_send['services'].push(service)
                        } else {
                            // Senão ja deve existir o Prot do Serviço
                            prot = service_list[i].querySelector('[name="cod"]')
                            prot = prot.getAttribute('value').trim().toUpperCase()
                            // Pegar dados do form
                            let itm_info_minuta = document.forms.itm_info_minuta

                            // Minuta
                            let minuta = service_list[i].querySelector('input[name="minuta_file"]')
                            if (minuta && minuta.files.length > 0) {
                                let reader = new FileReader()
                                reader.fileName = minuta.files[0].name
                                reader.fileType = minuta.files[0].type
                                reader.readAsDataURL(minuta.files[0])
                                reader['prot'] = prot
                                reader.onload = () => {
                                    reader['data'] = reader.result
                                        .replace('data:', '')
                                        .replace(/^.+,/, '')
                                }
                                const load_files = await loop_files([reader])
                                to_send['minuta'] = {
                                    'prot': prot,
                                    'fileName': reader.fileName,
                                    'fileType': reader.fileType,
                                    'data': reader.data,
                                }
                            }
                        }
                    }
                    break
                case 'cert':
                    if (nature == all_natures['attend']['cert']['Diligência']['id']) {
                        let pessoa = {}
                        // Coleta das informações
                        for (input of service_list[i].querySelectorAll('input')) {
                            // Resultado da Visita
                            if (input.type == 'radio') {
                                if (input.checked) {
                                    pessoa[input.name.split('_')[0]] = input.value
                                }
                            } else {
                                // Demais Inputs
                                if (input.value) pessoa[input.name.split('_')[0]] = input.value
                            }
                        }
                        // // Identificar CPF duplicado
                        // if (pessoa.cpf) {
                        //     pessoa['cpf'] = pessoa.cpf.replace(/\D/g, "")
                        //     if (cpf_list.includes(pessoa.cpf)) {
                        //         alert('CPF duplicado!')
                        //         return
                        //     }
                        //     cpf_list.push(pessoa.cpf)
                        // }
                        if (prot && prot.value) {
                            prot = prot.value.trim().toUpperCase()
                            if (prot.length != 17) {
                                alert('Código inválido.')
                                return
                            }
                            to_send['services'].push({
                                'type': stype,
                                'prot': prot,
                                'nature': nature,
                                'pessoa': pessoa,
                                // 'files': files,
                            })
                        } else {
                            // Nenhum resultado escolhido
                            if (!('result' in pessoa)) continue

                            // Validação das informações
                            requireds = ['name', 'cpf', 'dia', 'hora']
                            for (req of requireds) {
                                if (! Object.keys(pessoa).includes(req)) {
                                    alert(`Preencha todos os campos | ${req}`)
                                    return
                                }
                            }

                            // Comentário
                            let comment = service_list[i].querySelector(`#info_itm_comment_${i}`).value.trim()
                            if (comment) {
                                pessoa['comment'] = comment
                            }

                            // alert('Gravar visita se tiver')
                            to_send['pessoas'].push(pessoa)
                        }
                    }
                    continue
                    // break
            }
        }

        // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.post_comment') }}`
        fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(result)
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

var save_prot = async function(that) {
    // Services
    let service_list = $('itm_info_serv').children
    // Validando se primeiro serviço é o Protocolo
    let stype = service_list[0].attributes.value.value
    if (stype !== 'prot') {
        alert('Serviço incorreto, Prot não é o primeiro children')
        return
    }
    let prot = service_list[0].querySelector('input[name="cod"]')
    if (! prot.value.trim()) {
        alert('Protocolo não digitado.')
        return
    }
    prot = prot.value.trim().toUpperCase()
    if (! prot.length === 5 || ! prot.length === 6) {
        alert('Protocolo inválido.')
        return
    }

    let nature = service_list[0].querySelector('span.nature').attributes.value.value

    if (all_natures.ri[stype]['Intimação'].id !== nature) {
        alert(`Natureza do serviço ${prot} inválida save_prot`)
        return
    }

    let selo = service_list[0].querySelector('input[name="selo"]').value
    if (! selo) {
        alert('Selo não foi digitado')
        return
    } else if (selo.length != 23) {
        alert('Selo inválido')
        return
    }

    let prot_date = service_list[0].querySelector('input[name="date"]').value
    if (! prot_date) {
        alert('Entre com a data do protocolo')
        return
    }

    let to_send = {
        'id': that.name,
        'service': {
            'type': stype,
            'prot': prot,
            'nature': nature,
            'selo': selo,
            'prot_date': prot_date,
        },
    }

    let mat = service_list[0].querySelector('input[name="mat"]')
    if (mat) {
        to_send['service']['mat'] = mat.value.trim()
    }
   if (confirm('Deseja realmente SALVAR as alterações?')) {
        // Comment
        let comment = info_itm.querySelector('#itm_info_comment').value
        if (comment.trim()) {
            to_send['comment'] = comment.trim()
        }
        // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.post_service') }}`
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(result)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

var edit_minuta = async function(that) {

    to_send = {
        'id': intimacao.id,
        'devedores': [],
        'enderecos': [],
    }

        // Validações
    let file = itm_info_body.querySelector('input[name="prot_file"]')
    if (file.value.length) {
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
    }
    // Pegar dados do form
    let itm_info_minuta = document.forms.itm_info_minuta

    // Credor
    let credor_name = itm_info_minuta.querySelector('input[id="itm_credor_name"]')
    let credor_cnpj = itm_info_minuta.querySelector('input[id="itm_credor_cnpj"]')
    let credor_end = itm_info_minuta.querySelector('input[id="itm_credor_end"]')

    let selected = credor_name.list.querySelector(`option[value="${credor_name.value}"]`)
    if (selected) {
        to_send['credor'] = selected.dataset.value
    } else {
        to_send['credor'] = {
            'name': credor_name.value,
            'cnpj': credor_cnpj.value,
            'end': credor_end.value,
        }
        if (! (to_send['credor']['name'] && to_send['credor']['cnpj'] && to_send['credor']['end'])) {
            alert('Preencha todos os campos do Credor')
            return
        }
    }

    // Contrato
    let contr = itm_info_minuta.itm_credor_contr.value
    if (! contr || ! contr.trim()) {
        alert('Preencha o contrato')
        return
    }
    to_send['contr'] = contr.trim()

    // Devedores
    let devedores = itm_info_minuta.querySelector('#itm_info_minuta_devedores')
    let cancel = false
    for (d of devedores.children) {
        devedor = {}
        d.querySelectorAll('input').forEach(input => {
            let iname = input.name.split('_')[2]
            let ivalue = input.value.trim()
            if (! ivalue) {
                alert(`Preencha o campo: '${iname}'`)
                cancel = true
                return
            }
            if (iname == 'cpf') {
                ivalue = ivalue.replace(/\D/g,"")
            }
            devedor[iname] = ivalue
        })
        d.querySelectorAll('select').forEach(select => {
            let sname = select.name.split('_')[2]
            if(!select.value) {
                alert(`Preencha o campo: '${sname}'`)
                cancel = true
                return
            }
            devedor[sname] = select.value
        })

        to_send['devedores'].push(devedor)
        if (cancel) return
    }
    if (cancel) return
    // Endereços
    let enderecos = itm_info_minuta.querySelector('#itm_info_minuta_enderecos')
    cancel = false
    for (e of enderecos.children) {
        endereco = {}
        e.querySelectorAll('input').forEach(input => {
            let iname = input.name.split('_')[2]
            let ivalue = input.value.trim()
            if (! ivalue) {
                alert(`Preencha o campo: '${iname}'`)
                cancel = true
                return
            }
            if (iname == 'cep') {
                ivalue = ivalue.replace(/\D/g,"")
            }
            endereco[iname] = ivalue.replace(/"/g, '')
        })
        to_send['enderecos'].push(endereco)
    }
    if (cancel) return
    if (confirm('Deseja realmente SALVAR as alterações?')) {
        // Comment
        let comment = info_itm.querySelector('#itm_info_comment').value
        if (comment.trim()) {
            to_send['comment'] = comment.trim()
        }

        let mat = ''
        mat = info_itm.querySelector('#itm_info_mat').value
        if (mat.trim()) {
            to_send['mat'] = mat
        }
        // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.post_minuta') }}`
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                if (! selected) {
                    to_send['credor']['id'] = data['credor']
                    credores.push(to_send['credor'])
                }             
                open_itm_info(result)
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

const revis_minuta = function(that, id) {
    // Contrato
    let contr = itm_info_minuta.itm_credor_contr.value
    if (! contr || ! contr.trim()) {
        alert('Preencha o contrato')
        return
    }

    edit_minuta(itm_info_body.querySelector('.itm_info_btn_save'))
    if (confirm('Deseja realmente solicitar REVISÃO da minuta?')) {
        if (intimacao.services[0].total === intimacao.services[0].paid){
            // Send API
            let btn_html = that.innerHTML
            that.innerHTML = spinner_w
            let data = {
                'id': id,
                'action': 'pending',
            }
            let api_url = `{{ url_for('itm.put_minuta') }}`
            fetch(api_url, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                    body: JSON.stringify(data)})
            .then(response => response.json()).then(data => {
                result = data['result']
                if (result) {
                    itm_modal.hide()
                    load_itms()
                } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
                that.innerHTML = btn_html}
            }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
            that.innerHTML = btn_html})
        } else {
            alert('Confirmar pagamento pendente.')
        }
    }
}

const aprov_minuta = function(that, id) {
    if (confirm('Deseja realmente APROVAR a minuta?')) {
        // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let data = {
            'id': id,
            'action': 'confirm', 
        }
        let api_url = `{{ url_for('itm.put_minuta') }}`
        fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(data)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                itm_modal.hide()
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        }).catch(error => alert(`{{ _('Error in API') }} ${api_url} | ${error}`))
        .finally(() => that.innerHTML = btn_html)

    }
}
const save_selo_edital_info = async (that, id, svc) => {
    if (confirm('Deseja realmente GRAVAR o selo da PUBLICAÇÃO DE EDITAL?')) {
        // Send API
        if (intimacao.services[0].paid >= intimacao.services[0].total) {

            let oparent = that.closest('.info_itm_service_edital_selo')
    
            let btn_html = that.innerHTML
            that.innerHTML = spinner_w
            let to_send = {
                id,
                svc,
                'selo': oparent.querySelector('input[name="selo"]').value,
            }
            let api_url = `{{ url_for('itm.post_selo') }}`
            fetch(api_url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                    body: JSON.stringify(to_send)})
            .then(response => response.json()).then(data => {
                result = data['result']
                if (result) {
                    setTimeout(function() {
                        open_itm_info(id)
                    }, 1000)
                } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
            }).catch(error => alert(`{{ _('Error in API') }} ${api_url} | ${error}`))
            .finally(() => that.innerHTML = btn_html)
        } else {
            alert("Confirmar o PAGAMENTO da Publicação de Edital")
        }
    }
}

const save_dates_edital_info = async (that, id, svc) => {
    if (confirm('Deseja realmente GRAVAR os dados da PUBLICAÇÃO DE EDITAL?')) {
        let oparent = that.closest('.info_itm_service_edital_publicacao')

        // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let dia1 = oparent.querySelector('input[name="date-0"]').value
        let dia2 = oparent.querySelector('input[name="date-1"]').value
        let dia3 = oparent.querySelector('input[name="date-2"]').value
        let to_send = {
            id,
            svc,
            'dia1': dia1,
            'dia2': dia2,
            'dia3': dia3,
        }
        
        let file = oparent.querySelector('input[name="edital_itm_file"]').files 
        if (!file.length || file.length !== 3 ) {
            alert('Selecione todos os arquivos')
            return
        }
        // Para cada arquivo do input criar um item na lista uploads
        uploads = []
        for (var i = 0; i < file.length; i++) {
            let reader = new FileReader()
            reader.fileName = file[i].name
            reader.fileType = file[i].type
            reader.fileIndex = i
            reader.readAsDataURL(file[i])
            reader.onload = () => {
                reader['data'] = reader.result
                    .replace('data:', '')
                    .replace(/^.+,/, '')
            }
            uploads.push(reader)
        }
        const load_files = await loop_files(uploads)
        to_send['files'] = uploads
        let api_url = `{{ url_for('itm.post_edital') }}`
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                setTimeout(function() {
                    open_itm_info(id)
                }, 1000)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        }).catch(error => alert(`{{ _('Error in API') }} ${api_url} | ${error}`))
        .finally(() => that.innerHTML = btn_html)

    }
}

const rejec_minuta = function(that, id) {
    if (confirm('Deseja realmente REJEITAR a minuta?')) {
       // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let data = {
            'id': id,
            'action': 'reject',
            'values': []
        }

        let minuta_body = document.querySelector('#itm-minuta-prot-accordion-body')
        for(b of minuta_body.querySelectorAll('.btn-check')) {
            b.checked ? data.values.push(b.id.replace('btn-check_', '')) : ''
        }
        
        let api_url = `{{ url_for('itm.put_minuta') }}`
        fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(data)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                itm_modal.hide()
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

const info_print_minuta = function(that, id) {
    if (confirm('Deseja realmente CONFIRMAR a impressão da minuta?')) {
        // Send API
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let data = {
            'id': id,
            'action': 'print', 
        }
        let api_url = `{{ url_for('itm.put_minuta') }}`
        fetch(api_url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(data)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                itm_modal.hide()
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

function check_itm_info(that) {
    let cpf = mask_cpfcnpj(that.value)
    if ( cpf.length < 15 ) {
        that.value = cpf
        cpf=cpf.replace(/\D/g,"")
        if (cpf.length == 11) {
            if (! check_cpfcnpj(cpf)) {
                that.value = that.value.slice(0, -1)
                alert("CPF Inválido")
            }
        }
    } else {
        that.value = that.value.slice(0, -1)
    }
}

let keysPressed = {};

document.addEventListener('keydown', (event) => {
    keysPressed[event.key] = true;
    if (keysPressed['Control'] && event.code == 'Space') {
        itm_info_body.querySelector('.itm_info_btn_save').click()
    }
 });
 
document.addEventListener('keyup', (event) => {
delete keysPressed[event.key];
});

const save_visit = function(that, dev, posit) {
    let oparent = that.closest('.accordion-body')
    let end = oparent.querySelector('select[name="end_visit"]').value
    let dia = oparent.querySelector('input[name="dia"]').value
    let hora = oparent.querySelector('input[name="hora"]').value
    let result_select = oparent.querySelectorAll(`input[name="result_${posit}"]`)
    

    for (var i = 0; i < result_select.length; i++) {
        if (result_select[i].checked) {
            result = result_select[i].value
        }
    }

    if (! (end && dia && hora && result)) {
        alert('Preencha todos os campos obrigatórios')
        return
    }
    if (confirm('Deseja realmente SALVAR a Visita?')) {
        let to_send = {
            'dev': dev,
            'end': end,
            'date': `${dia}_${hora}`,
            'result': result,
        }
        let comment = oparent.querySelector('textarea[name="comment"]').value
        if (comment && comment.trim()) {
            to_send['comment'] = comment.trim()
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.post_visita') }}`
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                setTimeout(function() {
                    open_itm_info(intimacao.id)
                }, 1000)
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

const save_cert = async (that, dev, ind) => {
    let oparent = that.closest('.visit')
    let cod = oparent.querySelector('input[name="cod"]').value
    if (cod.length != 17) {
        alert("{{ _('Número do pedido inválido') }}")
        return
    }

    let file = oparent.querySelector(`#itm_file_${ind}`) 

    if (!file.value.length) {
        alert('Selecione os arquivos')
        return
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
    const load_files = await loop_files(uploads)

    


    if (confirm('Deseja realmente SALVAR a Certidão de DILIGÊNCIA?')) {
        let to_send = {
            'dev': dev,
            'cod': cod,
            'itm': intimacao.id,
            'file': uploads,
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.post_dili') }}` 
        
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(intimacao.id)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

{% if 'itm-sign' in roles %}
const undo_dili = (that, id) => {
    if (confirm('Deseja realmente DESFAZER a Certidão de DILIGÊNCIA?')) {
        let to_send = {
            'id': id,
            'itm': intimacao.id,
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.delete_dili') }}` //delete
        
        fetch(api_url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(intimacao.id)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}
{% endif %}

const delete_visit = (that, id, dev) => {
    if (confirm('Deseja realmente APAGAR a visita?')) {
        let to_send = {
            'id': id,
            'dev': dev,
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.delete_visita') }}` //delete
        
        fetch(api_url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(intimacao.id)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

const save_decur = async (that, id) => {
    let oparent = that.closest('.accordion-body')
    let cod = oparent.querySelector('input[name="cod"]').value
    if (cod.length != 17) {
        alert("{{ _('Número do pedido inválido') }}")
        return
    }
    if (confirm('Deseja realmente SALVAR a Certidão de DECURSO?')) {
        let to_send = {
            'cod': cod,
            'itm': id,
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('itm.post_decur') }}` 
        
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(intimacao.id)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}

function itm_info_add_payment(that, id) {
    if (confirm('Deseja realmente ADICIONAR um novo pagamento?')) {
        let value = that.closest('.itm_info_new_payment').querySelector('input[name="value"]').value.replace('.', '').replace(',', '.')
        let to_send = {
            'id': id,
            'value': value,
        }
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = `{{ url_for('finance.post_payment') }}` 
        
        fetch(api_url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                body: JSON.stringify(to_send)})
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_itm_info(id)
                load_itms()
            } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
            that.innerHTML = btn_html}
        }).catch(error => { alert(`{{ _('Error in API') }} POST ${api_url} | ${error}`) 
        that.innerHTML = btn_html})
    }
}