const logoutButton = document.querySelector('button');

logoutButton.onclick = async function () {

    const response = await fetch('/api/auth/logout', {
        method: 'POST',
    });

    if (response.status == 200) {
        window.location.href = '/';
    }
}