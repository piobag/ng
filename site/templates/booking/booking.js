const booking_services = {{ config['BOOKING_SERVICES']|tojson|safe }}
const bk_list = $('bookinglist-body')
const bookingform = document.forms.bookingform
const hours = bookingform.querySelector('#horas')

bookingform.day.addEventListener('change', () => calculate())

$('book-ri').innerHTML = Object.keys(booking_services).map(s => `
            <tr class="row justify-content-center">
                <td class="col-sm-9 d-flex flex-row justify-content-between">
                <div>
                    ${booking_services[s]['name']}
                </div>
                <div class="btn-group btn-group-sm justify-content-end" role="group">
                    <button type="button" class="btn btn-sm btn-outline-danger minus-button">-</button>
                    <input class="w-30 text-center service" onchange="calculate()" type="text" id="${s}" min="0" max="20" value="0" size="1">
                    <button type="button" class="btn btn-sm btn-outline-success plus-button">+</button>
                </div>
                </td>
            </tr>
            `).join('')

const services = document.getElementsByClassName('service')

document.querySelectorAll('.plus-button').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.previousElementSibling.value++
        calculate()
    })
})

document.querySelectorAll('.minus-button').forEach(btn => {
    btn.addEventListener('click', ()=>{
        btn.ementSibling.value = (btn.nextElementSibling.value == 0) ? 0 : btn.nextElementSibling.value - 1
        calculate()
    })
})

window.addEventListener('load', (event) => {
    reload_bookings()
    calculate()
})

function calculate() {
    let mins_total = 0
    for (let s in booking_services) {
        let v = services[s].value
        if (v > 0) {
            mins_total += v * booking_services[s]['mins']
        }
    }
    let day = new Date(`${bookingform.day.value}`).getTime() / 1000
    if (day) {
        if (mins_total > 0) {
            hours.innerHTML = spinner_w
            fetch("{{ url_for('booking.calc') }}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    "X-CSRFToken": "{{ csrf_token() }}" },
                body: JSON.stringify({
                    'day': day,
                    'mins': mins_total }) })
            .then(response => response.json()).then(data => {
                result = data['result']
                if (result) { hours.innerHTML = `
                    <label>{{ _('Hour') }}</label>
                    <select class="form-select form-select-sm required" name="hour" required>
                        ${result.map(h => `<option value="${h}">${h}</option>`).join('')}
                    </select>`
                } else { data['error'] ? hours.innerHTML = `<p><strong>${data['error']}</strong></p>` : hours.innerHTML = `<p>Unknown data: ${data}</p>`
                } })
            .catch(error => { hours.innerHTML = `<p>{{ _('Error in API') }} booking.calc | ${error}</p>` })
        } else {hours.innerHTML = "<p>{{ _('Choose the services') }}</p>"}
    } else {hours.innerHTML = "<p>{{ _('Choose a day') }}</p>"}
}

function new_booking() {
    if (bookingform.checkValidity() ) {
        let day = bookingform.day.value
        dateInPast = (testDate) => new Date(testDate) < new Date().setHours(0, 0, 0, 0)
        if (dateInPast(day.replace(/-/g, '\/'))) {
            alert("{{ _('Day in the past') }}")
            return
        }
        let hour = bookingform.hour.value
        if (! hour || ! hour.includes(':')) {
            alert("{{ _('Invalid time') }}")
            return
        }
        let values = {}
        for (let s in booking_services) {
            if (services[s].value > 0) {
                values[s] = services[s].value
            }
        }
        let btn_html = bookingform.btn.innerHTML
        bookingform.btn.innerHTML = spinner_w
        fetch("{{ url_for('booking.new') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": "{{ csrf_token() }}" },
            body: JSON.stringify({
                'name': bookingform.name.value,
                'day': day,
                'hour': hour,
                'services': values,
                'obs':  bookingform.obs.value }) })
        .then(response => response.json()).then(data => {
            result = data['result']
            if (result) {
                alert(result)
                bookingform.reset()
                reload_bookings()
                bootstrap.Modal.getInstance($('bookingnew')).hide()
                bootstrap.Modal.getOrCreateInstance($('bookinglist')).show()
                
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
            bookingform.btn.innerHTML = btn_html })
        .catch(error => {
            alert(`{{ ('Error in API') }} auth.get_users | ${error}`)
            bookingform.btn.innerHTML = btn_html })
    } else { alert('Preencha todos os campos.') }
}

function reload_bookings(page=1) {
    fetch(`{{ url_for('booking.index') }}?page=${page}`)
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            if (Array.isArray(result)) {
                bk_list.innerHTML = `{% include 'booking/booking_list.html' %}`
                if (data['next_url'] || data['prev_url']) {
                    bk_list.innerHTML = bk_list.innerHTML + `<br>
                        <nav>
                            <ul class="pagination justify-content-center">
                                <li class="page-item previous${data['prev_url'] ? '' : ' disabled'}">
                                    <button class="page-link" onclick="reload_bookings('${data['prev_url'] ? data['prev_url'] : '#'}')">{{ _('Previous') }}</button>
                                </li>
                                <li class="page-item next${data['next_url'] ? '' : ' disabled'}">
                                    <button class="page-link" onclick="reload_bookings('${data['next_url'] ? data['next_url'] : '#'}')">{{ _('Next') }}</button>
                                </li>
                            </ul>
                        </nav>`
                }
            } else {
                bk_list.innerHTML = '<p class="text-center"><b>{{ _("No appointments scheduled") }}</b></p>'
                let bookinglp = $('bookinglp')
                if (bookinglp) bookinglp.ref = '#bookingnew'
            }
        } else {
            data['error'] ? alert(data['error']) : console.error('Unknown data:', data) } })
    .catch(error => { alert(`{{ _('Error in API') }} booking.index | ${error}`) })
}

function delete_booking(id) {
    if (confirm("Deseja realmente cancelar o atendimento?")) {
        let btn_element = $('btn_'+id)
        let btn_html = btn_element.innerHTML
        btn_element.innerHTML = spinner_w
        fetch("{{ url_for('booking.delete') }}", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": "{{ csrf_token() }}" },
            body: JSON.stringify({ 'id': id }) })
        .then(response => response.json()).then(data => {
            if (data['result']) {
                load_attend()
            } else {
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                btn_element.innerHTML = btn_html
            }
        })
        .catch(error => {
            alert(`{{ _('Error in API') }} booking.delete | ${error}`)
            btn_element.innerHTML = btn_html })
    }
}
