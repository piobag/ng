window.addEventListener("load", (event) => {
    load_companys()
})

// Company List
let company_list_start = 0
let company_list_perpage = 5

function company_list_page(page) {
    company_list_start = (page*company_list_perpage)-company_list_perpage
    load_companys()
}
function company_list_change_perpage(that) {
    company_list_perpage = parseInt(that.value)
    // let length = sec_onr.querySelector(`#list_company_${filter}`).querySelector('.per_page').value
    load_companys()
}

function list_company(result){
    let last_page = parseInt(company_list_start)+parseInt(company_list_perpage)
    return `
        ${pagination(result['total'], 'company_list', company_list_start, company_list_perpage, result['filter'])}
            <table class="table table-sm table-hover table-responsive" style="min-width: 100%;">
                <thead>
                    <tr>
                        <th>Razão Social</th>
                        <th>{{ _('CNPJ') }}</th>
                        <th>{{ _('Email') }}</th>
                    </tr>
                </thead>
                <tbody>
                ${result.result.map(i => `
                    <tr onclick="open_company_info('${i.id}')">
                        <td>${i.name}</td>
                        <td><b><a><i class="fas fa-sm fa-arrow-alt-circle-right"></i> ${mask_cpfcnpj(i.cpfcnpj)}</a></b></td>
                        <td>${i.email}</td>
                    </tr>
                `).join('')}
                </tbody>
            </table>
            Filtrando de ${company_list_start+1} até ${parseInt(result['total']) < last_page ? result['total'] : last_page} do total de ${result['total']} itens. 
    `
}

async function load_companys(filter=null, start=company_list_start, length=company_list_perpage, search='', from='', end='') {
    let update_elem = $('company_update_btn')
    let update_html = update_elem.innerHTML
    update_elem.innerHTML = spinner_w

    let api_url = `{{ url_for('finance.get_companys') }}?start=${start}&length=${length}&search=${search}&filter=${filter}&from=${from}&end=${end}`
    // const resultcompanys = await 
    fetch(api_url)
    .then(response => response.json())
    .then(data => {
        result = data['result']
        if (result) {
            data['filter'] = filter
            let datalist_company = sec_finance.querySelector(`#company_info_list`)
            datalist_company.innerHTML = list_company(data)
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        } })
    .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
    .finally(() => { update_elem.innerHTML = update_html })
}

// Company New
const company_form_new = document.forms.company_new
company_form_new.cnpj.addEventListener('keyup', check_company)
function check_company() {
    let cnpj = mask_cpfcnpj(company_form_new.cnpj.value)
    company_form_new.cnpj.value = cnpj
    cnpj=cnpj.replace(/\D/g,"")

    if (cnpj.length == 14) {
        if (!check_cpfcnpj(cnpj)) {
            company_form_new.cnpj.value = company_form_new.cnpj.value.slice(0, -1)
            alert("CNPJ Inválido")
            return
        }
    } 
}

function save_company(that) {
    if (company_form_new.cnpj.value.length < 18) {
        alert('Digite CNPJ valido.')
        return
    }
    if (! company_form_new.email.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        alert("{{ _('Enter a valid email address') }}")
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let data = {
        'cnpj': company_form_new.cnpj.value.replace(/\D/g,""),
        'name': company_form_new.name.value,
        'tel': company_form_new.tel.value,
        'email': company_form_new.email.value,
    }
    let api_url = "{{ url_for('finance.post_company') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( data ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            load_companys()
            company_form_new.reset()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        that.innerHTML = btn_html })
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html
    })
}