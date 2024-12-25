// ### Datatable Natures ###
const nature_rowtemplate = (data) => {
    const html = `
        <tr onclick="open_nature_info('${data.id}')">
            <td>${data.name}</td>
            <td>${data.type === 'prot' ? 'Protocolo' : 'Certidão'}</td>
            <td>${data.group.toUpperCase()}</td>
        </tr>
    `;
    return html;
};
const nature_table = new DataTable({
    name: 'nature',
    apiEndpoint: '{{ url_for('attend.natures') }}',
    headers: ['Nome', 'Tipo', 'Grupo'],
    rowTemplate: nature_rowtemplate,
    spinner: true,
});
nature_table.init('#settings_natures_table', '#settings_natures_pagination', '#settings_natures_loading', '#settings_natures_error', '#settings_natures_search');
function nature_change_perpage(value) {
    let cur_item = nature_table.perPage * (nature_table.currentPage - 1) + 1
    nature_table.perPage = value
    let new_page = Math.ceil(cur_item / value)
    nature_table.currentPage = new_page
    nature_table.loadItems()
}

// ### Datatable Docuements ###
const document_rowtemplate = (data) => {
    const html = `
        <tr">
            <td>${data.name}</td>
        </tr>
    `;
    return html;
};
const document_table = new DataTable({
    name: 'document',
    apiEndpoint: '{{ url_for("attend.get_documents") }}',
    headers: ['Nome'],
    rowTemplate: document_rowtemplate,
});
document_table.init('#settings_documents_table', '#settings_documents_pagination', '#settings_documents_loading', '#settings_documents_error', '#settings_documents_search');
function document_change_perpage(value) {
    let cur_item = document_table.perPage * (document_table.currentPage - 1) + 1
    document_table.perPage = value
    let new_page = Math.ceil(cur_item / value)
    document_table.currentPage = new_page
    document_table.loadItems()
}


document.addEventListener("DOMContentLoaded", (event) => {
    get_users()
})
const sec_settings = $('settings')

// ### Users ###
let users_list_start = 0
let users_list_perpage = 10

const users_content = sec_settings.querySelector('#users_content')
const filtered_users = sec_settings.querySelector('#filtered_users')
const users_list = document.forms.users_list
let roles_div = sec_settings.querySelector('.roles-btns')

// colocar delay
users_list.search.addEventListener('keypress', (event) => {
    if(event.key === 'Enter') {
        event.preventDefault()
    }
})
users_list.search.addEventListener('keyup', () => {
    users_list_start = 0
    let filter = roles_div.querySelector('.btn-check:checked')
    filter ? get_users(filter.value) : get_users()
})
users_list.search.nextElementSibling.addEventListener('click', event => {
    users_list.reset()
    get_users()
})

for (a in auth_groups) {
    roles_input = document.createElement('input')
    roles_label = document.createElement('label')
    roles_input.classList.add('btn-check')
    roles_label.classList.add('btn', 'btn-outline-primary')
    roles_input.setAttribute('type', 'radio')
    roles_input.setAttribute('name', 'role-btn')
    roles_input.setAttribute('id', `role-btn_${auth_groups[a]}`)
    roles_label.setAttribute('for', `role-btn_${auth_groups[a]}`)
    roles_label.innerHTML = auth_groups[a]
    roles_input.value = a
    roles_div.append(roles_input, roles_label)
    roles_input.addEventListener('click', (event)=>{
        let filter = event.target.value
        users_list_start = 0
        get_users(filter)
    })
}

function users_list_page(page) {
    users_list_start = (page*users_list_perpage)-users_list_perpage
    let filter = roles_div.querySelector('.btn-check:checked')
    filter ? get_users(filter.value) : get_users()
}

function users_list_change_perpage(that) {
    users_list_perpage = parseInt(that.value)
    let filter = roles_div.querySelector('.btn-check:checked')
    filter ? get_users(filter.value) : get_users()
}

function get_users(filter) {
    let api_url = "{{ url_for('auth.get_users') }}?" + new URLSearchParams({
        'start': users_list_start,
        'length': users_list_perpage,
        'search': users_list.search.value,
        'filter': filter ? filter : ''
    })
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            let last_page = users_list_start+users_list_perpage
            users_content.innerHTML = `
                ${pagination(data['total'], 'users_list', users_list_start, users_list_perpage)}
                {% include 'auth/users.html' %}
            `
            users_content.querySelector('tbody').querySelectorAll('tr').forEach( tr => {
                tr.addEventListener('click', () => {
                    profile_body.innerHTML = spinner_b
                    profile_modal.show()
                    get_profile(tr.id)
                })
            })
        } else {data['error'] ? alert(data['error']) : console.error('Unknown data:', data) } })
    .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}

// ### Attend Natures ###
const natures_content = sec_settings.querySelector('#natures_content')
const filtered_natures = sec_settings.querySelector('#filtered_natures')
const total_natures = sec_settings.querySelector('#total_natures')

const natures_new = document.forms.natures_new
const documents_new = document.forms.documents_new

let nature_input = document.querySelectorAll('.natures_new')
for(n of nature_input) {
    n.addEventListener('keypress', (event)=> {
        if(event.key === 'Enter') {
            event.preventDefault()
            add_nature()
        }
    })
}

function add_nature() {
    let btn_html = natures_new.btn.innerHTML
    natures_new.btn.innerHTML = spinner_w
    let group = ''
    if (natures_new.nature_ri_group.checked){
        group = 'ri'
    } else if (natures_new.nature_rc_group.checked) {
        group = 'rc'
    } else if (natures_new.nature_rtd_group.checked) {
        group = 'rtd'
    } else {
        alert("Preencha todos os campos")
        natures_new.btn.innerHTML = btn_html
        return
    }

    let type
    if(natures_new.ri_prot.checked) {
        type = 'prot'
    } else if (natures_new.ri_cert.checked) {
        type = 'cert'
    } else {
        alert("Preencha todos os campos")
        natures_new.btn.innerHTML = btn_html
        return
    }

    fetch("{{ url_for('attend.new_nature') }}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": "{{ csrf_token() }}" },
        body: JSON.stringify({
            'name': natures_new.name.value,
            'group': group,
            'type': type
        })
    }).then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            nature_table.loadItems()
            natures_new.reset()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        natures_new.btn.innerHTML = btn_html
    }).catch(error => {
        alert(`{{ _('Error in API') }}: settings.nature ${error}`)
        natures_new.btn.innerHTML = btn_html
    })
}

let document_input = document.getElementById('document_input')
document_input.addEventListener('keypress', (event)=> {
    if(event.key === 'Enter') {
        event.preventDefault()
        add_document()
    }
})

function add_document() {
    let btn_html = documents_new.btn.innerHTML
    documents_new.btn.innerHTML = spinner_w
    fetch("{{ url_for('attend.new_document') }}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": "{{ csrf_token() }}" },
        body: JSON.stringify({
            'name': documents_new.name.value})
    }).then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            document_table.loadItems()
            documents_new.reset()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        documents_new.btn.innerHTML = btn_html
    }).catch(error => {
        alert(`{{ _('Error in API') }}: settings.document ${error}`)
        documents_new.btn.innerHTML = btn_html
    })
}



function del_nature(that) {
    if (confirm("Deseja realmente deletar a natureza?")) {
        fetch(`{{ url_for('attend.del_nature') }}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": "{{ csrf_token() }}"},
            body: JSON.stringify({'id': that.id})
        }).then(response => response.json()).then(data => {
            let msg = data['result']
            if (msg) {
                get_natures()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            }
        })
        .catch(error => { alert(`{{ _('Error in API') }} attend.del_nature | ${error}`) })
    }
}
