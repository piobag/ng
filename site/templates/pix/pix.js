window.addEventListener('load', (event) => {
    reload_pix()
    // let myModal = new bootstrap.Modal(document.getElementById('pixlist')).show()

})

function reload_pix() {
    $.ajax('/pix/').done(function(result) {
        document.getElementById('pixnew-body').innerHTML = result['new']
        document.getElementById('pixlist-body').innerHTML = result['list']
    })
}