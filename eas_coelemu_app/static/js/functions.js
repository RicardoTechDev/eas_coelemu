//Para los mensaje en pantalla
const SuccessSwal=(title)=>{
    Swal.fire({
        title: title,
        icon: 'success',
        confirmButtonColor: '#00D1B2',
        confirmButtonText: 'OK'
    })
};

const DeleteSwal=(title,text, url)=>{
    Swal.fire({
        title: title,
        text: text,
        icon: 'warning',
        showCancelButton: true,
        showLoaderOnConfirm: true,
        confirmButtonColor: '#00D1B2',
        confirmButtonText: '¡Si, eliminar!',
        cancelButtonText: 'Cancelar',
        }).then((result) => {
        if (result.isConfirmed) {
            location.href = url;
            Swal.fire({
                showConfirmButton : false,
                title: '¡Eliminado!',
                text: 'El registro ha sido eliminado.',
                icon: 'success',
            })
        }
        })
};


const UpdatedSwal=()=>{
    Swal.fire({
        title: '¿Seguro desea guardar los cambios?',
        showDenyButton: true,
        showCancelButton: true,
        confirmButtonText: 'Guardar',
        denyButtonText: `No Guardar`,
    }).then((result) => {
        /* Read more about isConfirmed, isDenied below */
        if (result.isConfirmed) {
            Swal.fire('Saved!', '', 'success')
        } else if (result.isDenied) {
            Swal.fire('Changes are not saved', '', 'info')
        }
    })
};


