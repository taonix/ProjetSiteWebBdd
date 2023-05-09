let questionnaireRempli = document.getElementById('questionnaireRempli');
let Gererlescomptes = document.getElementById('Gererlescomptes');

questionnaireRempli.onclick = function() {
    window.location.href = '/create_form';
};

Gererlescomptes.onclick = function() {
    window.location.href = '/accounts';
};

function rslt(questionnaireId) {
    window.location.href = '/reponses/'+questionnaireId+'/1';
}