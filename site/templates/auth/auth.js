const auth_modal = new bootstrap.Modal($('auth_modal'))

const forms = document.querySelectorAll("form")
const form_register = document.forms.register
const form_restore = document.forms.restore
const form_reset = document.forms.reset
const form_login = document.forms.login


form_register.cpf_reg.addEventListener('keyup', check_register)


function show(id) {
    forms.forEach((elem) => {
        if (elem.id == id) {
            elem.style.display = 'block'
        } else {
            elem.style.display = 'none'
        }
    })
}

document.querySelectorAll(".show_login").forEach((elem) => {
    elem.onclick = () => show('login')
})
document.querySelectorAll(".show_register").forEach((elem) => {
    elem.onclick = () => show('register')
})
document.querySelectorAll(".show_restore").forEach((elem) => {
    elem.onclick = () => show('restore')
})

function login(token=false) {
    if (form_login.cpf_log.value.length < 14) {
        alert("{{ _('Enter a valid cpf') }}")
        return
    }
    // if (! form_login.email_log.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
    //     alert("{{ _('Enter a valid email address') }}")
    //     return
    // }
    if (form_login.pwd_log.value.length < 8) {
        alert("{{ _('Password must be at least 8 characters long') }}")
        return
    }
    let btn_html = form_login.loginbtn.innerHTML
    form_login.loginbtn.innerHTML = spinner_w
    let api_url = "{{ url_for('auth.login') }}?next={{ next or '/' }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify({
            'token': token,
            'id': form_login.cpf_log.value.replace(/\D/g,""),
            'pwd': form_login.pwd_log.value,
            'remember': form_login.remember.checked})
    }).then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            window.location.replace(result)
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
            form_login.loginbtn.innerHTML = btn_html
    }).catch(error => {
        alert(`{{ _('Error in API') }}: auth.login ${error}`)
        location.reload()
    })
}

function check_login(event) {
    if (event.key === 'Enter') {
        event.preventDefault()
        form_login.loginbtn.click() 
    } else {
        let cpf = mask_cpfcnpj(form_login.cpf_log.value)
        if ( cpf.length < 15 ) {
            form_login.cpf_log.value = cpf
            cpf=cpf.replace(/\D/g,"")
            if (cpf.length == 11) {
                if (! check_cpfcnpj(cpf)) {
                    form_login.cpf_log.value = form_login.cpf_log.value.slice(0, -1)
                    alert("{{ _('Invalid CPF') }}")
                }
            }
        } else {
            form_register.cpf_reg.value = form_register.cpf_reg.value.slice(0, -1)
        }
    }
}

function register(token=false) {
    if (form_register.name_reg.value.length < 5) {
        alert("{{ _('Enter your full name') }}")
        return
    }
    if (form_register.cpf_reg.value.length < 14) {
        alert("{{ _('Invalid CPF') }}")
        return
    }
    if (! form_register.email_reg.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        alert("{{ _('Enter a valid email address') }}")
        return
    }
    if (form_register.pwd_reg.value.length < 8) {
        alert("{{ _('Password must be at least 8 characters long') }}")
        return
    }
    if (! (form_register.pwd_reg.value == form_register.pwd2_reg.value)) {
        alert(`{{ _("Passwords don't match") }}`)
        return
    }
    let btn_html = form_register.registerbtn.innerHTML
    form_register.registerbtn.innerHTML = spinner_w

    data = {
        'token': token,
        'name': form_register.name_reg.value,
        'cpf': form_register.cpf_reg.value.replace(/\D/g,""),
        'email': form_register.email_reg.value,
        'tel': form_register.tel_reg.value.replace(/\D/g,""),
        'pwd': form_register.pwd_reg.value,
        'pwd2': form_register.pwd2_reg.value,
    }
    api_url = "{{ url_for('auth.register') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": "{{ csrf_token() }}" },
        body: JSON.stringify(data),
    }).then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            alert(result)
            location.reload()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            form_register.registerbtn.innerHTML = btn_html
        }
    }).catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        form_register.registerbtn.innerHTML = btn_html
        // location.reload()
    })
}

function check_register(event) {
    if (event.key === 'Enter') {
        event.preventDefault(   )
        form_register.registerbtn.click() 
    } else {
        let cpf = mask_cpfcnpj(form_register.cpf_reg.value)
        if ( cpf.length < 15 ) {
            form_register.cpf_reg.value = cpf
            cpf=cpf.replace(/\D/g,"")
            if (cpf.length == 11) {
                if (! check_cpfcnpj(cpf)) {
                    form_register.cpf_reg.value = form_register.cpf_reg.value.slice(0, -1)
                    alert("{{ _('Invalid CPF') }}")
                }
            }
        } else {
            form_register.cpf_reg.value = form_register.cpf_reg.value.slice(0, -1)
        }
    }
}

function restore(token=false) {
    let form = document.forms.restore
    let cpf = form.cpf_res.value.replace(/\D/g,"")
    if (! check_cpfcnpj(cpf)) {
        alert("{{ _('Enter a valid cpf') }}")
        return
    }
    // if (! form.email_res.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
    //     alert("{{ _('Enter a valid email address') }}")
    //     return
    // }
    let btn_html = form.restorebtn.innerHTML
    form.restorebtn.innerHTML = spinner_w
    fetch("{{ url_for('auth.restore') }}", {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify({
            'token': token,
            'id': form.cpf_res.value })
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url
            return
        }
        response.json().then(data => {
            result = data['result']
            if (result) {
                alert(result)
                show('login')
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            }
            form.restorebtn.innerHTML = btn_html
        })
    }).catch(error => {
        alert(`{{ _('Error in API') }}: auth.restore ${error}`)
        location.reload()
    })
}

function check_restore(event) {
    if (event.key === 'Enter') {
        event.preventDefault()
        form_restore.restorebtn.click() 
    } else {
        let cpf = mask_cpfcnpj(form_restore.cpf_res.value)
        if ( cpf.length < 15 ) {
            form_restore.cpf_res.value = cpf
            cpf=cpf.replace(/\D/g,"")
            if (cpf.length == 11) {
                if (! check_cpfcnpj(cpf)) {
                    form_restore.cpf_res.value = form_restore.cpf_res.value.slice(0, -1)
                    alert("{{ _('Invalid CPF') }}")
                }
            }
        } else {
            form_restore.cpf_res.value = form_restore.cpf_res.value.slice(0, -1)
        }
    }
}

function check_reset(event) {
    if (event.key === 'Enter') {
        event.preventDefault(   )
        form_reset.resetbtn.click() 
    } else {
        let cpf = mask_cpfcnpj(form_reset.cpf_res.value)
        if ( cpf.length < 15 ) {
            form_reset.cpf_res.value = cpf
            cpf=cpf.replace(/\D/g,"")
            if (cpf.length == 11) {
                if (! check_cpfcnpj(cpf)) {
                    form_reset.cpf_res.value = form_reset.cpf_res.value.slice(0, -1)
                    alert("{{ _('Invalid CPF') }}")
                }
            }
        } else {
            form_reset.cpf_res.value = form_reset.cpf_res.value.slice(0, -1)
        }
    }
}


