import streamlit as st

st.title("Teste de Formulário")

with st.form("test_form"):
    st.text_input("Digite algo:", "Texto de teste")
    submit = st.form_submit_button("Enviar")

if submit:
    st.success("Formulário enviado com sucesso!")
    st.balloons() 