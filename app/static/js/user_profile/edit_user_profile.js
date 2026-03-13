const profilePictureSelect = document.getElementById('pfp')
const profilePictuerPreview = document.querySelector('.pfp-choice-img')

const sendButton = document.querySelector('button')

function updatePfp() {
    const selectedOption = profilePictureSelect.options[profilePictureSelect.selectedIndex]
    const link = selectedOption.getAttribute('data-link')
    profilePictuerPreview.src = link
}

async function sendData() {
    const userName = document.getElementById('name').value
    const bio = document.getElementById('bio').value
    const profilePictureId = parseInt(profilePictureSelect.value)

    const newData = {
        name: userName,
        bio: bio,
        profile_picture_id: profilePictureId
    };

    const response = await fetch(`/api/users/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newData)
    });
    
    if (response.ok) {
        window.location.href = `/users/${userId}`;
    } else {
        alert('An error occured when trying to update the profile.');
    }
}

profilePictureSelect.addEventListener('change', updatePfp)
sendButton.addEventListener('click', sendData)

updatePfp()