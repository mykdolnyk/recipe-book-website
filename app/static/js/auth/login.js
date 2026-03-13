const emailField = document.getElementById('email')
const passwordField = document.getElementById('password')
const signInButton = document.querySelector('button')
const formErrors = document.querySelector('.form-errors')
const errorList = formErrors.querySelector('ul')


signInButton.addEventListener('click', async (e) => {
    e.preventDefault(); 

    const email = emailField.value
    const password = passwordField.value

    if (!email || !password) {
        showErrors([{"msg": 'Email and password are required.'}]);
        return;
    }

    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({email, password}),
    });

    const data = await response.json(); // an object holding the errors array (and other data)

    if (response.ok) {
        window.location.href = '/';
    } else {
        if (data.errors) {
            // console.log(data.errors)
            showErrors(data.errors)
        } else {
            showErrors([{"msg": 'Login failed. Please try again.'}])
        }
    }

});

function showErrors(errors) {
    errorList.innerHTML = '';
    errors.forEach(error => {
        const li = document.createElement('li');

        let errorMsg
        if (error.loc && error.loc.length != 0) {
            errorMsg = `${capitalizeFirstLetter(error.loc).replace("_", " ")}: ${error.msg}`
        }
        else {
            errorMsg = `${error.msg}`
        }

        li.textContent = errorMsg
        errorList.appendChild(li);
    });
    formErrors.style.display = 'block';
    formErrors.style.height = 'auto';
}

function hideErrors() {
    formErrors.style.display = 'none';
    formErrors.style.height = '0';
}

function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
    // https://stackoverflow.com/a/1026087
}