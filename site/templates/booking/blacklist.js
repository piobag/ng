window.addEventListener('load', (event) => {
    load_blacklist()
})

const blacklist_new = document.forms.blacklist_new


let blacklist_input = document.getElementById('blacklist_input')
blacklist_input.addEventListener('keypress', (event)=> {
    if(event.key === 'Enter') {
        event.preventDefault()
        save_blacklist(this)
    }
})

function save_blacklist(that) {
    if (blacklist_new.name.value.length < 5) {
        alert('Digite um motivo maior para o Blacklist.')
        return
    }
    if (blacklist_new.start.value == '' || blacklist_new.end.value == '') {
        alert('Digite o intervalo de dias que não haverá serviço.')
        return
    }
    if (blacklist_new.start.value > blacklist_new.end.value) {
        alert('O dia final não pode ser antes do dia inicial!')
        return
    }
    let btn_html = that.innerHTML
    that.innerHTML = spinner_w

    let api_url = "{{ url_for('booking.post_blacklist') }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( {
            'name': blacklist_new.name.value,
            'start': blacklist_new.start.value,
            'end': blacklist_new.end.value,
        } ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            if (result > 0) {
                if (confirm('Já existem '+result+' agendamento(s) para o dia. Todos serão cancelados com o motivo informado.')) {
                    let api_url = "{{ url_for('booking.post_blacklist') }}"
                    fetch(api_url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
                        body: JSON.stringify( {
                            'name': blacklist_new.name.value,
                            'start': blacklist_new.start.value,
                            'end': blacklist_new.end.value,
                            'force': true,
                        } ) })
                    .then(response => response.json()).then(data => {
                        if (data['result']) {
                            blacklist_new.reset()
                            load_blacklist()
                        } else {
                            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                        }
                        reload_blacklist(true)
                        reload_bookings()
                    })
                }
            } else {
                blacklist_new.reset()
                load_blacklist()
            }
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
        }
        that.innerHTML = btn_html })
    .catch(error => {
        alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html
    })
}

function load_blacklist() {
    let api_url = "{{ url_for('booking.get_blacklist') }}"
    fetch(api_url)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            $('blacklist_list').innerHTML = `
                ${result.map(b => `
                    <tr>
                        <td>${b.name}</td>
                        <td>${new Date(b.start * 1000).toLocaleString('default', { dateStyle: 'short', timeZone: 'UTC' })}</td>
                        <td>${new Date(b.end * 1000).toLocaleString('default', { dateStyle: 'short', timeZone: 'UTC' })}</td>
                        <td>
                            <button type="button" onclick="delete_blacklist(this, '${b._id.$oid}')" class="btn btn-sm btn-outline-danger"><i class="fa fa-sm fa-trash"></i></button>
                        </td>
                    </tr>
                `).join('')}`
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })
}

function delete_blacklist(that, bid) {
    if (confirm("Deseja realmente APAGAR o blacklist?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w
        let api_url = "{{ url_for('booking.delete_blacklist') }}"
        fetch(api_url, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( {'delete': bid} ) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                load_blacklist()
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


