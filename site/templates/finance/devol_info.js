const devol_modal = new bootstrap.Modal($('devol_info_modal'))

function open_devol_modal(id) {
    devol_modal.show()
    let devol_btn_status = ''
    let devol_body = $("devol_info_body")
    devol_body.innerHTML = spinner_w

    let api_url = `{{ url_for('finance.get_devol') }}?id=${id}`
    fetch (api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            switch (result['choice']) {
                case 'transf':
                    devol_btn_status = `
                        <h5>{{ _('Bank transfer') }}</h5>
                        <div>
                        <div>{{ _('Bank') }} | <b>${result['transf']['banco']}</b></div>
                        <div>{{ _('Agency') }} | <b>${result['transf']['agencia']}</b></div>
                        <div>{{ _('Account') }} | <b>${result['transf']['tipo'] == 'c' ? 'Corrente' : result['transf']['tipo'] == 'p' ? 'Poupança' : 'Tipo de conta não identificado'} - ${result['transf']['conta']}</b></div>
                        </div>
                        <div>
                        ${result['file'] ? `<img class="img-fluid" src="{{ url_for('finance.get_devol_file') }}?id=${id}">` : `
                        <form id="upload_devol">
                            <input name="id" value="${id}" hidden>
                            <input type="file" id="devol_file" name="devol_file" accept=".jpg,.jpeg,.png,.gif" onchange="devol_file_preview(event)" style="display: none;">
                            <label class="btn btn-sm btn-outline-primary" for="devol_file">
                                <i class="fas fa-sm fa-upload"></i>
                            </label>
                            <div id="devol_file_preview"></div>
                        </form>
                        </div>
                        `}
                    `
                    break
                case 'retire':
                    devol_btn_status = `
                        <h5>{{ _('Withdrawal at Reception') }}</h5>
                        
                        <button class="btn btn-sm btn-outline-danger" onclick="confirm_retire(this, '${id}')"><i class="fas fa-money-check-alt"></i></button>`
                    break
                case 'reprot':
                    devol_btn_status = `<h5>{{ _('Reprotocol') }}</h5>
                    `
                    break
                default:
                    devol_btn_status = `
                        <h5>{{ _('Resend email') }}</h5>

                        <button class="btn btn-sm btn-outline-warning" onclick="resend_devol(this, '${result['id']}')"><i class="fa fa-sm fa-envelope"></i></button>
                    `
                    break
            }
            devol_body.innerHTML = `{% include "finance/devol_info_content.html" %}`
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            devol_modal.hide() }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        devol_modal.hide() })
}


function resend_devol(that, id) {
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    if (confirm("Deseja reenviar o email?")) {
        let api_url = "{{ url_for('finance.put_devol') }}"
        fetch(api_url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'resend': id} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                alert('Email enviado com sucesso!')
                that.innerHTML = btn_html
                devol_modal.hide()
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


function devol_file_preview(event){
    if(event.target.files.length > 0){
        let preview = $("devol_file_preview")
        preview.innerHTML = ''
        let img = document.createElement("img")
        Object.assign(img, {
            className: 'img-fluid',
            src: URL.createObjectURL(event.target.files[0]),
            width: 800
        })
        preview.appendChild(img)
        preview.insertAdjacentHTML('beforeend', `
            <div><button type="button" class="btn btn-sm btn-outline-success" onclick="upload_devol(this)"><i class="fas fa-sm fa-save"></i></button></div>`)
    }
}

function upload_devol(that) {
    let form = document.forms.upload_devol
    if (form.devol_file.files.length < 1) {
        alert('{{ _("Please insert a file") }}')
        return
    }

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let api_url = "{{ url_for('finance.post_devol_file') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { "X-CSRFToken": csrf_token },
        body: new FormData(form) })
    .then(response => response.json()).then(data => {
        // if (data.status == 413) {alert('Arquivo muito grande para ser enviado.')}

        if (data['result']) {
            open_devol_modal(form.id.value)
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            that.innerHTML = btn_html }})
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html
    })
}


