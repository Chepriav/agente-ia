export let currentLang = 'es';

export const i18n = {
  es: {
    org_label: 'Organización',
    org_placeholder: 'policia-nacional',
    load_btn: 'Cargar',
    docs_label: 'Documentos indexados',
    docs_subtitle: 'Documentos disponibles para consulta en esta organización',
    docs_empty: 'No hay documentos indexados todavía.',
    upload_label: 'Subir documento',
    upload_subtitle: 'PDF o Word. Se indexa automáticamente para consulta.',
    upload_cta: 'Arrastra o haz clic',
    upload_formats: 'PDF · DOCX',
    chat_title: 'Consultar base de conocimiento',
    chat_ready: 'Listo',
    chat_welcome: 'Hola. Puedo responder preguntas sobre los documentos de esta organización. ¿En qué puedo ayudarte?',
    chat_placeholder: 'Escribe tu pregunta...',
    toast_loaded: 'Organización cargada',
    toast_uploaded: 'Documento indexado correctamente',
    toast_error: 'Error al procesar el documento',
    toast_org_error: 'No se pudo cargar la organización',
    thinking: 'Consultando documentos...',
  },
  en: {
    org_label: 'Organization',
    org_placeholder: 'national-police',
    load_btn: 'Load',
    docs_label: 'Indexed documents',
    docs_subtitle: 'Documents available for queries in this organization',
    docs_empty: 'No documents indexed yet.',
    upload_label: 'Upload document',
    upload_subtitle: 'PDF or Word. Automatically indexed for queries.',
    upload_cta: 'Drag or click',
    upload_formats: 'PDF · DOCX',
    chat_title: 'Query knowledge base',
    chat_ready: 'Ready',
    chat_welcome: "Hello. I can answer questions about this organization's documents. How can I help you?",
    chat_placeholder: 'Type your question...',
    toast_loaded: 'Organization loaded',
    toast_uploaded: 'Document indexed successfully',
    toast_error: 'Error processing document',
    toast_org_error: 'Could not load organization',
    thinking: 'Querying documents...',
  },
};

export function t(key) {
  return i18n[currentLang][key] || key;
}

export function setLang(lang) {
  currentLang = lang;
  document.querySelectorAll('.lang-btn').forEach(b => {
    b.classList.toggle('active', b.textContent === lang.toUpperCase());
  });
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
}
