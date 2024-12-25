window.onload = function (){
    load_finance()
}

let finance = {}

let load_finance = (that, args=false) => new Promise(resolv => {
    let api_url = "{{ url_for('finance.index') }}"

    let btn_html = false
    if (that) {
        btn_html = that.outerHTML
        that.onclick = ''
        that.innerHTML = spinner_w
    }

    if (args) api_url += `?${args}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            finance = result
            sec_finance.querySelector('#devol_nature_list').innerHTML = Object.keys(all_natures['attend']['prot']).map(n => `<option data-value="${ all_natures['attend']['prot'][n].id }" value="${ n }"></option>`).join('')
            let finance_balance_amount = sec_finance.querySelector('#finance_balance_amount')
            finance_balance_amount.innerHTML = ''
            // Total Payments
            // console.log(result['total_payments'])
            for (const [key, value] of Object.entries(result['total_payments'])) {
                finance_balance_amount.insertAdjacentHTML('beforeend', `
                    <div id='div_pay' class="item" onclick="pay_html(this)">
                        <span id='span_pay'>${all_payments[key.split('_')[0]].name} ${key.split('_').length > 1 ? key.split('_')[1] : '' }</span>
                        ${key.split('_')[0] === 'cd' ? 
                            `<b>${value.toLocaleString('pt-BR', currency_br)} | ${(add_payment_percent(value, 0.55) + value).toLocaleString('pt-BR', currency_br)} </b>` : 
                            `<b>${value.toLocaleString('pt-BR', currency_br)}</b>`}
                    </div>`)
            }

            let finance_balance_itens = sec_finance.querySelector('#finance_balance_itens')
            finance_balance_itens.innerHTML = ''

            for (const [key, value] of Object.entries(result['users'])) {
                // User Payments
                let user_payments = ''
                for (ptype of Object.keys(value['payments'])) {
                    user_payments += `
                        <div class="item">
                            <span>${all_payments[ptype.split('_')[0]].name} ${ptype.split('_').length > 1 ? ptype.split('_')[1] : '' }</span> <br>
                            ${ptype.split('_')[0] === 'cd' ? 
                            `<b>${value['payments'][ptype].toLocaleString('pt-BR', currency_br)}</b> | ${(add_payment_percent(value['payments'][ptype], 0.55) + value['payments'][ptype]).toLocaleString('pt-BR', currency_br)}` : 
                            `<b>${value['payments'][ptype].toLocaleString('pt-BR', currency_br)}</b>`}
                        </div>
                    `
                }
                // User Balance
                let user_balance = ''
                if (value['attends'] && Object.values(value['attends']).length) {
                    user_balance += ` 
                        <br><h4>RI - Atendimentos</h4>
                        <table class="table table-sm table-hover table-responsive">
                            <thead>
                                <tr>
                                    <th scope="col">Data</th>
                                    <th scope="col">Nome</th>
                                    <th scope="col">CPF</th>
                                    <th scope="col">Email</th>
                                    <th scope="col">Pago</th>
                                </tr>
                            </thead>
                            <tbody>
                            ${Object.keys(value['attends']).map(item => `
                                <tr onclick="open_attend_info('${value['attends'][item]['id']}')">
                                    <td>${new Date(value['attends'][item]['end'] * 1000).toLocaleString('default', { dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</td>
                                    <td>${value['attends'][item]['name']}</td>
                                    <td>${mask_cpfcnpj(value['attends'][item]['cpf'])}</td>
                                    <td>${value['attends'][item]['email']}</td>
                                    <td>${value['attends'][item]['paid'].toLocaleString('pt-BR', currency_br)}</td>
                                </tr>
                            `).join('')}
                            </tbody>
                        </table>
                    `
                }

                // Intimações
                if (value['itms'] && Object.values(value['itms']).length) {
                    user_balance += `
                        <br><h4>ONR - Intimações</h4>
                        <table class="table table-sm table-hover table-responsive table-onr">
                            <thead>
                                <tr>
                                    <th scope="col">Data</th>
                                    <th scope="col">Código</th>
                                    <th scope="col">Pago</th>
                                    <th scope="col">Orçado</th>
                                </tr>
                            </thead>
                            <tbody>
                            ${Object.values(value['itms']).map(itm => `
                                <tr onclick="open_itm_info('${itm['id']}')">
                                    <td>${new Date(itm['start'] * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</td>
                                    <td><b><a><i class="fas fa-sm fa-arrow-alt-circle-right"></i> ${itm['itm']}</a></b></td>
                                    <td>${itm['paid'].toLocaleString('pt-BR', currency_br)}</td>
                                    <td>${itm['orcado'].toLocaleString('pt-BR', currency_br)}</td>
                                </tr>
                            `).join('')}
                            </tbody>
                        </table>
                    `
                }
                // Serviços
                if (value['services'] && Object.values(value['services']).length) {
                    user_balance += `
                        <br><h4>ONR - Serviços</h4>
                        <table class="table table-sm table-hover table-responsive table-onr">
                            <thead>
                                <tr>
                                    <th scope="col">Data</th>
                                    <th scope="col">Código</th>
                                    <th scope="col">Tipo</th>
                                    <th scope="col">Natureza</th>
                                    <th scope="col">Valor</th>
                                </tr>
                            </thead>
                            <tbody>
                            ${value['services'].map(s => `
                                <tr onclick="open_itm_info('${s['id']}')">
                                    <td>${new Date(s['date'] * 1000).toLocaleString('default', {dateStyle: 'short', timeZone: 'America/Sao_Paulo' })}</td>
                                    <td><b><a><i class="fas fa-sm fa-arrow-alt-circle-right"></i> ${s['prot']}</a></b></td>
                                    <td>${all_services[s['type']]['name']}</td>
                                    <td>${s['nature']}</td>
                                    <td>${s['paid'].toLocaleString('pt-BR', currency_br)}</td>
                                </tr>
                            `).join('')}
                            </tbody>
                        </table>
                    `
                }
                // Insert HTML
                finance_balance_itens.insertAdjacentHTML('beforeend', `
                    <div class="accordion-item accordion-border">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed text-center" type="button" data-bs-toggle="collapse" data-bs-target="#acc_${key}" aria-expanded="false" aria-controls="acc_${key}">
                                <h2 class="accordion_title">${value['name']}</h2>
                            </button>
                        </h2>
                        <div id="acc_${key}" class="accordion-collapse collapse" data-bs-parent="#finance_balance_itens">
                            <div class="accordion-body">
                                <div class="user_balance_amount">
                                    ${user_payments}
                                </div>
                                <span id="balance_user_${key}">
                                    ${user_balance}
                                </span>
                            </div>
                        </div>
                    </div>`
                )
            }
            resolv()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data) 
        } })
    .catch(error => {
        console.log(`{{ _('Error in API') }} ${api_url} | ${error}`) })
    .finally(() => { if (that) {that.outerHTML = btn_html} })
})

function pay_html(that) {
    let name = that.querySelector('#span_pay').innerHTML;
    let name_trim = name.trim()
    for (let i in all_payments) {
        if (name_trim === all_payments[i].name) {
            search = that.closest('.accordion-body').querySelector('.fa-search').parentElement
            filter_balance(search, i)
            return
        }
    }
}

const find_bal = document.forms.find_balance
let filter_balance = async function(that, filter=false) {
    from = find_bal.date_start.value
    console.log(from)
    end = find_bal.date_end.value
    if (end && ! from) {
        alert('Selecione a data inicial.')
        return
    }
    if (from && end && from > end) {
        alert('O dia final não pode ser antes do dia inicial!')
        return
    }
    let args = []
    from ? args.push(`from=${from}`) : '' 
    end ? args.push(`end=${end}`) : ''
    filter ? args.push(`filter=${filter}`) : ''
    const call_load_finance = await load_finance(that, args.length > 0 ? args.join('&') : false)
}

function print_balance(that) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    // let finance_list = JSON.parse(finance);
    
    let balance_users = ''
    for (const [key, value] of Object.entries(finance.users)) {
        let finance_list = ''
        for (ptype of Object.keys(value['payments'])) {
            finance_list += `
            <tr style="border-bottom: 0.1rem solid black;">
                <td>${all_payments[ptype.split('_')[0]].name} ${ptype.split('_').length > 1 ? ptype.split('_')[1] : '' }</td>
                <td>${ptype.split('_')[0] === 'cd' ? 
                    `${value['payments'][ptype].toLocaleString('pt-BR', currency_br)} | ${(add_payment_percent(value['payments'][ptype], 0.55) + value['payments'][ptype]).toLocaleString('pt-BR', currency_br)} ` : 
                    `${value['payments'][ptype].toLocaleString('pt-BR', currency_br)}`}
                </td>
            </tr>
        `
        }
        finance_list += `
            <tr>
                <td><b>Total</b></td>
                <td>${Object.values(value['payments']).reduce((a,b) => a += ( b ), 0).toLocaleString('pt-BR', currency_br)}</td>
            </tr>
        `
        balance_users += `
                        <div style="display: flex; justify-content: end; width: 580px;">
                            <span style="font-size: 12px; margin: 6px;">${value.name}: ___________________________________________________</span>
                        </div>
                        <table style="font-size: 9px; width: 180px;">
                            <tbody>
                                ${finance_list}
                            </tbody>
                        </table>
                    `

    }
    var doc = new jsPDF({
        unit: "pt",
        format: "a4"
    })
    let print_date = ''
        if (find_bal.date_start.value) {
            print_date = new Date(find_bal.date_start.value + 'T00:00:00-03:00').toLocaleString('default', {dateStyle: 'long', timeZone: 'America/Sao_Paulo'})
        } else {
            print_date = new Date().toLocaleString('default', {dateStyle: 'long', timeZone: 'America/Sao_Paulo'})
        }
    let print_content = `{% include 'finance/recibo.html' %}`
    that.innerHTML = btn_html
    doc.html(print_content, {
      callback: function () {
        doc.save("finance.pdf")
      },
    })
    
}





{% include 'finance/devol/devol.js' %}

{% include 'finance/company/company.js' %}


