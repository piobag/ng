window.addEventListener('load', (event) => {
    load_audit()
})

const list_devreport = $('list_devreport')
function load_audit() {
    let api_url = "{{ url_for('audit.get_dev') }}"
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            $('list_devreport_total').innerHTML = `<b>Saldo: ${data['balance']}</b>`
            for (let rel of result) {
                list_devreport.insertAdjacentHTML('beforeend', `
                <tr>
                    <td>${new Date(rel.date * 1000).toLocaleString('default', {dateStyle: 'long', timeZone: 'UTC' })}</td>
                    <td><b>${rel.hours}</b> Horas</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <a class="btn btn-sm btn-outline-success" href="{{ url_for('audit.get_dev_doc') }}?id=${rel.id}" target="_blank" rel="noopener noreferrer">
                                <i class="fas fa-sm fa-download"></i>
                            </a>
                            <button type="button" onclick="delete_devreport(this, '${rel.id}')" class="btn btn-sm btn-outline-danger"><i class="fa fa-sm fa-trash"></i></button>
                        </div>
                    </td>
                </tr>`)
            }
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        } })
    .catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}

const devreport = document.forms.devreport
function new_devreport(that) {
    if (! devreport.checkValidity()) {
        alert('Preencha todos os campos.')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let formData = new FormData(devreport)
    let api_url = "{{ url_for('audit.new_dev') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { "X-CSRFToken": csrf_token },
        body: formData })
    .then(response => response.json()).then(data => {
        if (data['result']) {
            load_audit()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        that.innerHTML = btn_html})
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html 
    })
}
