function send_contact() {
    let form = document.forms.contact
    if (form.name.value.length < 4) {
        alert("{{ _('Enter a valid name') }}")
        return
    }
    if (! form.email.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        alert("{{ _('Enter a valid email address') }}")
        return
    }
    if (form.message.value.length < 8) {
        alert("{{ _('Please enter a longer message so we can answer you') }}")
        return
    }
    let btn = form.querySelector('button')
    btnhtml = btn.innerHTML
    btn.innerHTML = spinner_w
    fetch("{{ url_for('base.contact') }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": "{{ csrf_token() }}" },
        body: JSON.stringify({
            'name': form.name.value,
            'email': form.email.value,
            'tel': form.tel.value,
            'type': form.type.value,
            'subject': form.subject.value,
            'message': form.message.value }) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            btn.innerHTML = btnhtml
            btn.onclick = function() { alert('Sua mensagem já foi enviada, aguarde nossa resposta.') }
            alert(result)
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            btn.innerHTML = btnhtml } })
    .catch(error => {
        alert(`{{ _('Error in API') }} app.index | ${error}`)
        btn.innerHTML = btnhtml })
}
