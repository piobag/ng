
const info_nature = $('nature_info_modal')


const nature_modal = new bootstrap.Modal(sec_settings.querySelector('#nature_info_modal'))
const nature_info_body = sec_settings.querySelector('#nature_info_body')

function edit_nature(that, id) {
    let nature_info_doc = sec_settings.querySelector('#nature_info_doc').querySelectorAll('input');
    let docs = [];
    nature_info_doc.forEach(checkbox => {
        if (checkbox.checked) {
            docs.push(checkbox.id);
        }
    });
    let to_send = {id,docs}
    
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    fetch("{{ url_for('attend.put_nature') }}", {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": "{{ csrf_token() }}" },
        body: JSON.stringify(to_send)
    }).then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            nature_modal.hide()
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        that.innerHTML = btn_html
    }).catch(error => {
        alert(`{{ _('Error in API') }}: attend.put_nature ${error}`)
        that.innerHTML = btn_html
    })
}

function disable_nature(that, id) {
    if (confirm("Deseja realmente DELETAR a natureza?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        // Criar Rota para desativar natureza
        fetch("{{ url_for('attend.del_nature') }}", {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": "{{ csrf_token() }}" },
            body: JSON.stringify({id})
        }).then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                nature_modal.hide()
                nature_table.loadItems()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
            }
            that.innerHTML = btn_html
        }).catch(error => {
            alert(`{{ _('Error in API') }}: attend.del_nature ${error}`)
            that.innerHTML = btn_html
        })
    }
}


function open_nature_info(id) {
    nature_modal.show()
    nature_info_body.innerHTML = spinner_b
    
    let api_url = `{{ url_for('attend.nature_info') }}?id=${id}`
    
    fetch(api_url)
    .then(response => response.json()).then(data => {
        let result = data['result']
        if (result) {
            nature_info_body.innerHTML = `{% include 'settings/info/nature.html' %}`
            let api_document_url = `{{ url_for('attend.get_documents') }}?length=99999`
            fetch(api_document_url)
            .then(response => response.json()).then(docdata => {
                let doc_result = docdata['result']
                if (doc_result) {

                    let nature_info_doc = sec_settings.querySelector('#nature_info_doc')
                    nature_info_doc.innerHTML = `
                        <table class="table">
                            <tbody>
                                ${doc_result.map(p => `
                                    <tr>
                                        <td>
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" ${p.active == 'true' ? 'checked' : ''} id="${p.id}">
                                                <label class="form-check-label" for="${p.id}">
                                                    <h5>${p.name}</h5>
                                                </label>
                                            </div>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    
                    `
                    let nature_doc = nature_info_doc.querySelectorAll('input')
                    nature_doc.forEach(doc => {
                        for ( d of result.docs ) {
                            if ( d.id === doc.id ) {
                                doc.checked = true
                            }
                        }
                    });

                } else { docdata['error'] ? alert(docdata['error']) : console.log('Unknown docdata:', docdata) }
            }).catch(error => { alert(`{{ _('Error in API') }} GET ${api_url} | ${error}`) })
        } else { data['error'] ? alert(data['error']) : console.log('Unknown data:', data) }
    }).catch(error => { alert(`{{ _('Error in API') }} GET ${api_url} | ${error}`) })
}
