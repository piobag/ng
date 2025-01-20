window.addEventListener("load", (event) => {
    {% if config.DEBUG %}
        // open_attend_info('678aad62ec11f9f0e149665a')
    {% endif %}
})

const attend_modal = new bootstrap.Modal(sec_info.querySelector('#attend_info_modal'))
const attend_info_body = sec_info.querySelector('#attend_info_body')

let info_valid_form_erro = false

function open_attend_info(id) {
    let api_url = `{{ url_for('attend.get_info') }}?id=${id}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            attend = result
            // console.log(result)
            // History
            attend_comments = ''
            for (e of result['history']) {
                switch (e.action) {
                    case 'end':
                        text = `<span>Finalizou <b>atendimento</b> de </span> <span><b>${e.target['name']}</b> | ${mask_cpfcnpj(e.target['cpf'])}.</span>`
                        break
                    case 'create':
                        if (e.object == 'service') {
                            text = `<span>Criou o serviço <b>${e.target.prot}</b> no valor de: <b>${e.target.total.toLocaleString('pt-BR', currency_br)}</b>.`
                        } else if (e.object == 'payment') {
                            text = `<span>Adicionou o pagamento "<b>${all_payments[e.target.type].name}</b>" no valor de <b>${e.target.value.toLocaleString('pt-BR', currency_br)}</b>.`
                        }
                        break
                    case 'comment':
                        text = `<span>Adicionou o <b>comentário:</b> ${e.target['comment']}.`
                        break
                    case 'confirm':
                        text = `<span>Confirmou <b>${all_payments[e.target.type].name}</b> no valor de <b>${e.target['value'].toLocaleString('pt-BR', currency_br)}</b>.</spam>`
                        break
                    case 'company':
                        text = `<span>Vinculou a empresa <b>credênciada</b> ao atendimento.</spam>`
                        break
                    case 'pay':
                        text = `<span>Pagou a diferença do serviço <b>${e.target.prot}</b> no valor de <b>${e.target['paying'] ? e.target['paying'].toLocaleString('pt-BR', currency_br) : ''}</b>.</spam>`
                        break
                    case 'delete':
                        text = `<span>Deletou <b>${all_payments[e.target.type].name}</b> no valor de <b>${e.target['value'].toLocaleString('pt-BR', currency_br)}</b>.</spam>`
                        break
                    case 'value':
                        text = `<span>Alterou o <b>valor</b> do protocolo ${e.target.prot} de <b>${e.target.total.toLocaleString('pt-BR', currency_br)}</b> para <b>${e.target.new_value.toLocaleString('pt-BR', currency_br)}</b></spam>`
                        break
                    case 'edit':
                        text = `<span>Alterou o <b>código</b> do protocolo de <b>${e.target.prot}</b> para <b>${e.target.new_cod}</b></spam>`
                        break
                    default:
                        text = 'Evento <b>desconhecido</b>'
                        break
                }
                attend_comments += `
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
            var prot_ven = ''
            var prot_emi = ''
            var prot_date = ''
            for (s of attend.services) {
                if (s.prot_emi) {
                    prot_emi = new Date(s.prot_emi * 1000) 
                }
                if (s.prot_ven) {
                    prot_ven = new Date(s.prot_ven * 1000) 
                }
                if (s.prot_date) {
                    prot_date = new Date(s.prot_date * 1000) 
                }
            }
            attend_info_body.innerHTML = `{% include "attend/info/content.html" %}`
            attend_modal.show()
            
            // document.getElementById("attend_info_print").click()
        } else {
            data['error'] ? alert(data['error']) : console.log('Unknown data:', data)
            that.innerHTML = btn_html
        }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) 
                        that.innerHTML = btn_html})
}


function info_attend_cpfcnpj(that) {
    let cpfcnpj = mask_cpfcnpj(that.value);

    // Atualiza o valor do campo com a máscara aplicada
    that.value = cpfcnpj;

    // Remove caracteres não numéricos
    cpfcnpj = cpfcnpj.replace(/\D/g, "");

    if (cpfcnpj.length === 14) {
        // Validação para CNPJ
        if (!check_cpfcnpj(cpfcnpj)) {
            that.value = that.value.slice(0, -1);
            alert("CNPJ Inválido");
        }
    } else if (cpfcnpj.length > 14) {
        // Impede a inserção de mais caracteres além do limite
        that.value = that.value.slice(0, -1);
    }
}


function info_attend_print(that) {
    info_save_attend(attend_info_body.querySelector('#info_save_btn_attend'), 'edit');
    
    if (info_valid_form_erro) {
        console.warn('Formulario com um problema.');
        return;
    } else {
        let btn_html = that.innerHTML;
        that.innerHTML = spinner_w;

        var doc = new jsPDF({
            unit: "pt", // Unidade em pontos
            format: "a4" // Formato A4
        });

        setTimeout(function () {
            let print_content = `{% include 'attend/info/print_attend.html' %}`;
            that.innerHTML = btn_html;

            doc.html(print_content, {
                callback: function () {
                    // Salvar o PDF
                    doc.save(`${s.prot_cod}.pdf`);
                    
                    // Informar à API que o documento foi impresso
                    let to_send = {
                        'id': s.id,
                        'action': 'print',
                    };

                    let api_url = "{{ url_for('attend.put_prot') }}";
                    fetch(api_url, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            "X-CSRFToken": csrf_token
                        },
                        body: JSON.stringify(to_send)
                    })
                        .then(response => response.json())
                        .then(data => {
                            let result = data['result'];
                            if (! result) {
                                // Exibir erro
                                data['error'] ? alert(data['error']) : console.error('Unknown data:', data);
                                that.innerHTML = btn_html;
                            }
                        })
                        .catch(error => {
                            alert(`{{ _('Error in API') }}: settings.document ${error}`);
                            that.innerHTML = btn_html;
                        });
                }
            });
        }, 1000);
    }


}



function info_save_attend(that, action) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let to_send = {
        'id': s.id,
        'action': action,
    }
    if (action === 'edit') {
        if (confirm("Deseja realmente SALVAR alterações?")) {
            info_valid_form_erro = false
            let attend_info_form = document.forms.info_attend
            attend_info_form.querySelectorAll('input').forEach(elem => {
                if(elem.value){
                    if(elem.name === 'prot_val' || elem.name === 'prot_tot_c' || elem.name === 'prot_tot_p'){
                        to_send[elem.name] = parseFloat(elem.value.replace(/[^\d.,]/g, '').replace('.', '').replace(',', '.'))
                    } else if (elem.name === 'prot_emi' || elem.name === 'prot_date' || elem.name === 'prot_ven') {
                        // Criar um objeto ajustado para Brasília
                        let date = new Date(`${elem.value}T00:00:00-03:00`);
                        to_send[elem.name] = date.getTime() / 1000
                        // Obter o timestamp (em milissegundos desde 1970)
                    } else if (elem.name === 'prot_cod') {
                        to_send[elem.name] = parseFloat(elem.value)
                    } else if (elem.name === 'end_cep' || elem.name === 'prot_num') {
                        to_send[elem.name] = parseFloat(elem.value.replace(/[\D]+/g,''))
                    } else if (elem.name === 'prot_sac_doc') {
                        to_send[elem.name] = elem.value.replace(/[\D]+/g,'')
                    } else if (elem.name === 'id') {
                        to_send['attend'] = elem.value
                    } else {
                        to_send[elem.name] = elem.value
                    }
                } else {
                    if(elem.name !== 'prot_ven') {
                        info_valid_form_erro = true
                        that.innerHTML = btn_html;
                        return
                    }
                }
            })
            if (info_valid_form_erro) {
                alert('Preencha todos os campos do formulário')
                return
            }
        } else {
            that.innerHTML = btn_html
            return
        }
    } else if (action === 'take') {
        if (! confirm("Deseja realmente MARCAR serviço como ENTREGUE?")) {
            that.innerHTML = btn_html
            return
        }
    } else if (action === 'paid') {
        if (! confirm("Deseja realmente MARCAR serviço como PAGO?")) {
            that.innerHTML = btn_html
            return
        }
    }
    let api_url = "{{ url_for('attend.put_prot') }}"
    fetch(api_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(to_send) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            open_attend_info(attend.id)
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            that.innerHTML = btn_html
        }})
    .catch(error => {
        alert(`{{ _('Error in API') }}: settings.document ${error}`)
        that.innerHTML = btn_html
    })
}



