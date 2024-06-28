document.addEventListener('DOMContentLoaded', () => {
    let lastRequest = 0;
    const codeButton = document.getElementById('get-code');
    const timeInterval = 120;
    codeButton.addEventListener('click', () => {
        let emailInput = document.getElementById('email');
        if (!emailInput.checkValidity()) {
            alert('邮箱格式错误');
            return;
        }
        const currentTime = new Date().getTime();
        if (currentTime - lastRequest < timeInterval * 1000) {
            return;
        }
        lastRequest = currentTime;
        fetch(emailValidateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
            })
        }).then(response => response.json()).then(data => {
            console.log(data);
            if (data.status == 'success') {
                alert('验证码已发送，请查收');
            } else {
                alert('验证码发送失败，请检查邮箱是否正确');
            }
        })
    }
    );
})