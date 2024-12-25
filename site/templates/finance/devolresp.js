window.addEventListener('load', (event) => {
    $("devol_modal_body").innerHTML = `{% include "finance/devolresp.html" %}`
    devol_modal.show()
})

const devol = {{ devol | tojson | safe }}

const devol_modal = new bootstrap.Modal($('devolresp'))
const devolrtransf = document.forms.devolrespform

function devolresp(that, choice) {

    let data = {'choice': choice}
    if (choice == 'transf') {
        // criar mascara para codigo verificador e só aceitar numero na agencia
        let devolrtransf = document.forms.devolrespform
        if (devolrtransf.banco.value.length < 3 ) {
            alert('{{ _("Please enter the bank name correctly") }}')
            return
        }  
        if (! devolrtransf.conta_c.checked && ! devolrtransf.conta_p.checked) {
            alert('{{ _("Please select account type") }}')
            return
        }   
        if (devolrtransf.agencia.value.length < 4 ) {
            alert('{{ _("Please enter the agency number correctly") }}')
            return
        }  
        if (devolrtransf.conta.value.length < 5 ) {
            alert('{{ _("Please enter the account number correctly") }}')
            return
        }       

        data = {...data,
            'banco': devolrtransf.banco.value,
            'tipo': devolrtransf.conta_c.checked ? 'c' : 'p',
            'agencia': devolrtransf.agencia.value,
            'conta': devolrtransf.conta.value,
        }    
    }

    let btn_html = that.innerHTML
    that.innerHTML = spinner_w
    
    let api_url = "{{ url_for('finance.devol_resp', token=token) }}"
    fetch(api_url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
        body: JSON.stringify( data ) })
    .then(response => response.json()).then(data => {
        result = data['result']
        if (result) {
            devol_modal.hide()
        } else { data['error'] ? alert(data['error']) : console.error('Unknown data:', data) }
        that.innerHTML = btn_html
    }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`)
        that.innerHTML = btn_html })
}


function devolrespback() {
    document.getElementById('devolrespback').style.display = 'none'
    document.getElementById('devolrespopt').style.display = 'block'
    document.getElementById('t-body').style.display = 'none'
    document.getElementById('r-body').style.display = 'none'
    document.getElementById('p-body').style.display = 'none'
}
function transfer() {
    document.getElementById('devolrespopt').style.display = 'none'
    document.getElementById('devolrespback').style.display = 'block'
    document.getElementById('t-body').style.display = 'block'
}
function retire() {
    document.getElementById('devolrespopt').style.display = 'none'
    document.getElementById('devolrespback').style.display = 'block'
    document.getElementById('r-body').style.display = 'block'
}
function reprot() {
    document.getElementById('devolrespopt').style.display = 'none'
    document.getElementById('devolrespback').style.display = 'block'
    document.getElementById('p-body').style.display = 'block'
}


