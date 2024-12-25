const sec_finance = $('finance')

const company_modal = new bootstrap.Modal(sec_finance.querySelector('#fin_company_modal'))
const company_info_body = sec_finance.querySelector('#fin_company_body')

const open_company_info = (id) => {
    let api_url = `{{ url_for('finance.get_company') }}?id=${id}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            let users = ''
            if (result.users.length) {
                users += `
                    <table class="table table-sm table-hover table-responsive" style="min-width: 100%;">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>CPF</th>
                                <th>Email</th>
                                <th>Telefone</th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.users.map(i => `
                                <tr>
                                    <td>${i.name}</td>
                                    <td><b><a><i class="fas fa-sm fa-arrow-alt-circle-right"></i> ${mask_cpfcnpj(i.cpfcnpj)}</a></b></td>
                                    <td>${i.email}</td>
                                    <td>${mtel(i.tel)}</td>
                                    <td><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('finance.get_company_user') }}?id=${result.id}&user=${i.id}" target="_blank" rel="noopener noreferrer"><i class="fas fa-sm fa-download"></i></a></td>
                                    <td><button tabindex="-1" type="button" class="btn btn-sm btn-outline-danger" onclick="del_company_rep(this, '${result.id}', '${i.cpfcnpj}')"><i class="fas fa-sm fa-trash"></i></button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `
            }
            let company_pay = ''
            if (result.payments.length) {
                company_pay += result.payments.map(i => i.confirmed ? `
                                <tr>
                                    <td>${new Date(i.timestamp * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</td>
                                    <td>${i.desc ? i.desc : i.type}</td>
                                    <td>${i.value.toLocaleString('pt-BR', currency_br)}</td>
                                    <td><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('finance.get_company_file') }}?id=${i.id}" target="_blank" rel="noopener noreferrer"><i class="fas fa-sm fa-download"></i></a></td>
                                </tr>
                            `: '').join('')
            }

            let company_debit = ''
            if (result.payments.length) {
                company_debit += result.services.map(i => `
                                <tr>
                                    <td>${new Date(i.date * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo'})}</td>
                                    <td>${i.prot}</td>
                                    <td>${i.paid.toLocaleString('pt-BR', currency_br)}</td>
                                </tr>
                            `).join('')
            }
            let total_pay = 0
            total_pay = result.payments.reduce((a,b) => a += b.confirmed ? b.value : 0, 0)
            
            let total_debit = 0
            total_debit = result.services.reduce((a,b) => a += b.paid, 0)

            let balance = total_pay-total_debit
            
            total_debit = total_debit.toLocaleString('pt-BR', currency_br)
            total_pay = total_pay.toLocaleString('pt-BR', currency_br)
            balance = balance.toLocaleString('pt-BR', currency_br)

            let entradas = ''
            if (result.payments.length) {
                entradas += `
                    <div class="info_company_payment">
                        <h5><b>Entradas</b></h5>
                        <table class="table table-sm table-hover table-responsive">
                            <thead>
                                <tr>
                                <th>Data</th>
                                <th>Descrição</th>
                                <th>Valor</th>
                                <th></th>
                                </tr>
                            </thead>
                            <tbody>
                            ${company_pay}
                            </tbody>
                            <tfoot>
                            <td></td>
                            <td>Total</td>
                            <td><b>${total_pay}</b></td>
                            <td></td>
                            </tfoot>
                            
                        </table>            
                    </div>
            `}
            let saidas = ''
            if (result.services.length) {
                saidas += `
                <div class="info_company_payment">
                    <h5><b>Saídas</b></h5>
                    <table class="table table-sm table-hover table-responsive">
                        <thead>
                            <tr>
                            <th>Data</th>
                            <th>Protocolo</th>
                            <th>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                        ${company_debit}
                        </tbody>
                        <tfoot>
                        <td></td>
                        <td>Total</td>
                        <td><b>${total_debit}</b></td>
                        </tfoot>
                        
                    </table>            
                </div>
            `}
            company_info_body.innerHTML = `{% include "finance/company/info_cont.html" %}`
            company_modal.show()
            let file_dep = company_info_body.querySelector('#comp_comprov')
            file_dep.addEventListener('change', (event) => {
                const files = event.target.files
                let filename = company_info_body.querySelector('#info_comp_file_list')
                filename.innerHTML = ''
                for (const file of files) {
                  const li = document.createElement('li');
                  li.textContent = file.name;
                  li.className = 'list-group-item list-group-item-action'
                  filename.appendChild(li)
                }
            })

            let file_rep = company_info_body.querySelector('#comp_rep_comp')
            file_rep.addEventListener('change', (event) => {
                const files = event.target.files
                let filename = company_info_body.querySelector('#comp_rep_file')
                filename.innerHTML = ''
                for (const file of files) {
                  const li = document.createElement('li');
                  li.textContent = file.name;
                  li.className = 'list-group-item list-group-item-action'
                  filename.appendChild(li)
                }
            })

        } else {
            data['error'] ? alert(data['error']) : console.log('Unknown data:', data)
        }
    }).catch(error => { alert(`{{ _('Error in API') }} GET ${api_url} | ${error}`) })
}
const deposit_company_info = async (that, id) => {
    let comp_form = document.forms.info_comp_content
    let desc = comp_form.comp_desc.value
    if (!desc) {
        alert('Informe a descrição do depósito')
        return
    }
    let value = comp_form.comp_value.value
    if (!value) {
        alert('Informe o valor do depósito')
        return
    }
    let file = comp_form.comp_comprov
    if (!file.files.length) {
        alert('Selecione o comprovante do depósito')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    let data = {
        'id': id,
        'desc': desc,
        'value': value.replace('.', '').replace(',', '.'),
    }
    let reader = new FileReader()
    reader.fileName = file.files[0].name
    reader.fileType = file.files[0].type
    reader.readAsDataURL(file.files[0])
    reader.onload = () => {
        reader['data'] = reader.result
            .replace('data:', '')
            .replace(/^.+,/, '')
    }
    const load_filepay = await loop_files([reader])
    data['compr'] = reader
    let api_url = "{{ url_for('finance.post_company_payment') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify(data) })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            open_company_info(id)
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
    that.innerHTML = btn_html})
}

const check_company_rep = (that) => {
    let cpf = mask_cpfcnpj(that.value) 
    that.value = cpf
    cpf=cpf.replace(/\D/g,"")
    if (cpf.length == 11) {
        if (check_cpfcnpj(cpf)) {
            let api_url = `{{ url_for('auth.get_id') }}?id=${cpf}`
            fetch(api_url)
            .then(response => response.json()).then(data => {
                if (data['result']) {
                    let new_company_rep = document.forms.info_comp_content
                    new_company_rep.name.value = data['result']['name']
                    // new_company_rep.email.value = data['result']['email']
                    // new_company_rep.tel.value = mtel(data['result']['tel'])
                } else if (data['noresult']) {
                    new_company_rep.name.value = ''
                    // new_company_rep.email.value = ''
                    // new_company_rep.tel.value = ''
                    alert('CPF não está cadastro no sistema')
                } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
            }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
        } else {
            that.value = that.value.slice(0, -1)
            alert("{{ _('Invalid CPF') }}")
        }
    }
}

const create_company_rep = async (that, id) => {
    if (confirm("Deseja realmente VINCULAR o USUÀRIO a Empresa?")) {
        let comp_form = document.forms.info_comp_content
             
        let cpf = comp_form.cpf.value
        if (!cpf) {
            alert('Informe o CPF do representante')
            return
        }
        let data = {
            'id': id,
            'user': cpf.replace(/\D/g,""),
        }
        let file = comp_form.comp_rep_comp
        if (!file.files.length) {
            alert('Selecione o comprovante do depósito')
            return
        }

        
        let reader = new FileReader()
        reader.fileName = file.files[0].name
        reader.fileType = file.files[0].type
        reader.readAsDataURL(file.files[0])
        reader.onload = () => {
            reader['data'] = reader.result
                .replace('data:', '')
                .replace(/^.+,/, '')
        }
        const load_filepay = await loop_files([reader])
        data['compr'] = reader

        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
       
        let api_url = "{{ url_for('finance.post_company_user') }}"
        fetch(api_url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( data ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_company_info(id)
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html })
    }
}

const del_company_rep = (that, id, cpf) => {
    if (confirm("Deseja realmente DESVINCULAR o USUÀRIO a Empresa?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let data = {
            'id': id,
            'user': cpf,
        }
        let api_url = "{{ url_for('finance.delete_company_user') }}"
        fetch(api_url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( data ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                open_company_info(id)
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html })
    }
}