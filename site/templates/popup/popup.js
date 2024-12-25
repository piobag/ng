const popup_new = document.forms.popup_new
window.addEventListener('load', () => {
    {% for option in config['POPUP_ROUTES'] %}
        opt = document.createElement("option")
        opt.value = "{{ option }}"
        opt.text = "{{ config['POPUP_ROUTES'][option] }}"
        popup_new.page.add(opt, null)
    {% endfor %}
    load_popup()
})

function load_popup() {
    let api_url = "{{ url_for('popup.index') }}"
    fetch(api_url)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            $('popups_table_list').innerHTML = `
                ${result.map(p => `
                    <tr>
                        <td>${p.name}</td>
                        <td>${p.route}</td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <button type="button" onclick="view_popup(this, '${p.id}')" title="Pré-visualizar" class="btn btn-sm btn-outline-primary"><i class="fa fa-sm fa-eye"></i></button>
                                ${p.active ? `<button type="button" onclick="disable_popup(this, '${p.id}')" title="Ativado" class="btn btn-sm btn-outline-success"><i class="fa fa-sm fa-check-circle"></i></button>
                                ` : `<button type="button" onclick="enable_popup(this, '${p.id}')" title="Desativado" class="btn btn-sm btn-outline-warning"><i class="fa fa-sm fa-ban"></i></button>`}
                                <button type="button" onclick="delete_popup(this, '${p.id}')" class="btn btn-sm btn-outline-danger"><i class="fa fa-sm fa-trash"></i></button>
                            </div>
                        </td>
                    </tr>
                `).join('')}`
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}

let popup_input = document.getElementById('popup_input')
popup_input.addEventListener('keypress', (event)=> {
    if(event.key === 'Enter') {
        event.preventDefault()
        new_popup(this)
    }
})

function new_popup(that) {
    if (! popup_new.checkValidity()) {
        alert('Preencha todos os campos.')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let formData = new FormData(popup_new)
    formData.append('active', popup_new.popup_btn_active.checked)
    let api_url = "{{ url_for('popup.new') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { "X-CSRFToken": csrf_token },
        body: formData })
    .then(response => response.json()).then(data => {

        // if (data.status == 413) {alert('Arquivo muito grande para ser enviado.')}

        if (data['result']) {
            popup_new.reset()
            load_popup()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        that.innerHTML = btn_html})
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html
    })
}

const popup_show = new bootstrap.Modal($('popup_show'))
function view_popup(that, pid) {
    $('popup_show_content').innerHTML = `<img src="{{ url_for('popup.view') }}?id=${pid}" class="img-fluid rounded mx-auto d-block">`;
    popup_show.show()
}

function enable_popup(that, pid) {
    if (confirm("Deseja realmente ATIVAR o popup?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
    
        let api_url = "{{ url_for('popup.edit') }}"
        fetch(api_url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'enable': pid} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                load_popup()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html
        })
    }
}

function disable_popup(that, pid) {
    if (confirm("Deseja realmente DESATIVAR o popup?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w

        let api_url = "{{ url_for('popup.edit') }}"
        fetch(api_url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'disable': pid} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                load_popup()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html
        })
    }
}

function delete_popup(that, pid) {
    if (confirm("Deseja realmente APAGAR o popup?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w

        let api_url = "{{ url_for('popup.delete') }}"
        fetch(api_url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'delete': pid} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                load_popup()
                // that.closest('tr').remove()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }})
        .catch(error => {
            alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
            that.innerHTML = btn_html
        })
    }
}

