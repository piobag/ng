const profile_modal = new bootstrap.Modal($('profile'))
const profile_body = $('profile-body')


// document.addEventListener("DOMContentLoaded", (event) => {
//     {% if not current_user.cpfcnpj %}
//         get_profile(user_id='{{ current_user.id }}', force=true)
//     {% else %}
//         get_profile()
//     {% endif %}

//     // $('#profile').on('hidden.bs.modal', function () {
//     //     get_profile()
//     // })
// })

function check_profile() {
    let profile_form = document.forms.profileform
    let cpf = mask_cpfcnpj(profile_form.cpfcnpj.value)
    if ( cpf.length < 15 ) {
        profile_form.cpfcnpj.value = cpf
        cpf=cpf.replace(/\D/g,"")
        if (cpf.length == 11) {
            if (! check_cpfcnpj(cpf)) {
                profile_form.cpfcnpj.value = profile_form.cpfcnpj.value.slice(0, -1)
                alert("{{ _('Invalid CPF') }}")
            }
        }
    } else {
        profile_form.cpfcnpj.value = profile_form.cpfcnpj.value.slice(0, -1)
    }
}

function get_profile(user_id='{{ current_user.id }}', force=false, ferias=false) {
    let api_url = `{{ url_for('auth.get_user') }}?id=${user_id}`
    fetch(api_url)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            console.log(result)
            if (result['admissao']) {
                let admissao = new Date(result['admissao'] * 1000)
                result['admissao'] = admissao.toISOString().split('T')[0]
            }
            profile_body.innerHTML = `{% include 'auth/profile.html' %}`
            if (force) {
                profile_modal._config['backdrop'] = 'false'
                document.getElementById('closeprofile').outerHTML = `
                        <a id="logout_profile" href="{{ url_for('auth.logout') }}">
                            <button type="button" class="btn btn-sm btn-danger">
                                Logout
                            </button>
                        </a>`
                profile_modal.show()
                alert('Preencha seu CPF ou CNPJ para continuar.')
            }
            if (ferias) ferias_profile()
            profile_modal.show()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}

function save_profile() {
    let profile_form = document.forms.profileform
    if (profile_form.name.value.length < 4) {
        alert('Digite seu nome completo.');
        return
    }
    if (! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile_form.email.value)) {
        alert('Email inválido!');
        return
    }

    if (profile_form.cpfcnpj.value.length < 14) {
        alert("{{ _('Invalid CPF') }}")
        return
    }
    let data = {
        'id': profile_form.id.value,
        'name': profile_form.name.value,
        'tel': profile_form.tel.value.replace(/\D/g,""),
        'email': profile_form.email.value,
        'cpfcnpj': profile_form.cpfcnpj.value.replace(/\D/g,""),
    }
    if (profile_form.lunch) {
        if (profile_form.lunch.value) {
            data['lunch'] = profile_form.lunch.value
        } else {
            data['lunch'] = '00:00'
        }
    }
    if (profile_form.admissao) {
        if (profile_form.admissao.value) {
            data['admissao'] = profile_form.admissao.value
        } else {
            data['admissao'] = ''
        }
    }
    let groups_e = $('groups')
    if (groups_e) {
        let groups = []
        groups_e.querySelectorAll('input').forEach(elem => {
            if (elem.checked) { groups.push(elem.id.split('_')[1]) }
        })
        data['groups'] = groups
    }
    if (profile_form.confirmed && profile_form.confirmed.checked) {
        data['confirmed'] = profile_form.confirmed.checked
    }
    console.log(data)
    btn = $('profilebtn')
    btn_html = btn.innerHTML
    btn.innerHTML = spinner_w
    fetch("{{ url_for('auth.put_user') }}", {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": "{{ csrf_token() }}" },
        body: JSON.stringify( data ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            // location.reload()
            profile_modal.hide()
            let logout_profile = $('logout_profile')
            if (logout_profile) {

                profile_modal._element.setAttribute('data-bs-backdrop', 'true')
                // _config['backdrop'] = 'true'
                logout_profile.outerHTML = '<button id="closeprofile" type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>'
                {% if not 'adm' in roles %}
                    profile_form.cpfcnpj.disabled = 'true'
                {% endif %}

            }
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        btn.innerHTML = btn_html
    }).catch(error => {
        alert(`{{ _('Error in API') }} auth.users | ${error}`)
        btn.innerHTML = btn_html
    })
}
