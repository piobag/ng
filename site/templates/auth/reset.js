const form = document.forms.reset

function reset_pwd(token) {
    if (form.pwd.value.length < 8) {
        alert("{{ _('Password must be at least 8 characters long') }}")
        return
    }
    if (form.pwd.value != form.pwd2.value) {
        alert(`{{ _("Passwords don't match") }}`)
        return
    }
    let btn_html = form.resetbtn.innerHTML
    form.resetbtn.innerHTML = spinner_w
    fetch(`{{ url_for('auth.reset', token=token) }}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify({
            'token': token,
            'pwd': form.pwd.value,
            'pwd2': form.pwd2.value
        })
    }).then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            alert(result)
            window.location.replace("{{ url_for('base.index') }}?show=auth_modal")
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            form.registerbtn.innerHTML = btn_html
        }
    }).catch(error => {
        alert(`{{ _('Error in API') }} auth.register | ${error}`)
        location.reload()
    })
}


