// Estado da aplicação
const state = {
    currentStep: 1,
    totalSteps: 5,
    data: {
        categoria: null,
        status: null,
        motivo: null,
        valorPedido: null,
        tempoEspera: null,
        descricao: null
    }
};

// Mapeamentos de labels
const labels = {
    categoria: {
        'cancelamento': 'Cancelamento',
        'entrega': 'Entrega',
        'cobranca': 'Cobrança',
        'fraude': 'Segurança',
        'qualidade': 'Qualidade',
        'atraso': 'Atraso'
    },
    status: {
        'AGUARDANDO_CONFIRMACAO': 'Aguardando confirmação',
        'EM_PREPARO': 'Em preparo',
        'SAIU_PARA_ENTREGA': 'Saiu para entrega',
        'ENTREGUE': 'Entregue',
        'CANCELADO': 'Cancelado'
    },
    motivo: {
        'ARREPENDIMENTO_CLIENTE': 'Mudei de ideia',
        'CANCELAMENTO_RESTAURANTE': 'Restaurante cancelou',
        'ERRO_APP': 'Erro no aplicativo',
        'TEMPO_MUITO_LONGO': 'Tempo de espera muito longo',
        'PEDIDO_NAO_CHEGOU': 'Pedido não chegou',
        'PEDIDO_ERRADO': 'Pedido veio errado',
        'PEDIDO_INCOMPLETO': 'Pedido incompleto',
        'PEDIDO_DANIFICADO': 'Pedido danificado',
        'COBRANCA_DUPLICADA': 'Cobrança duplicada',
        'COBRANCA_INDEVIDA': 'Cobrança indevida',
        'COMPRA_NAO_RECONHECIDA': 'Compra não reconhecida',
        'CONTA_INVADIDA': 'Conta invadida',
        'COMIDA_FRIA': 'Comida fria',
        'COMIDA_ESTRAGADA': 'Comida estragada',
        'ATRASO_EXCESSIVO': 'Atraso excessivo',
        'OUTRO': 'Outro motivo'
    }
};

// Motivos por categoria
const motivosPorCategoria = {
    cancelamento: [
        { value: 'ARREPENDIMENTO_CLIENTE', label: 'Mudei de ideia' },
        { value: 'CANCELAMENTO_RESTAURANTE', label: 'Restaurante cancelou' },
        { value: 'ERRO_APP', label: 'Erro no aplicativo' },
        { value: 'TEMPO_MUITO_LONGO', label: 'Tempo de espera muito longo' }
    ],
    entrega: [
        { value: 'PEDIDO_NAO_CHEGOU', label: 'Pedido não chegou' },
        { value: 'PEDIDO_ERRADO', label: 'Pedido veio errado' },
        { value: 'PEDIDO_INCOMPLETO', label: 'Pedido incompleto' },
        { value: 'PEDIDO_DANIFICADO', label: 'Pedido chegou danificado' }
    ],
    cobranca: [
        { value: 'COBRANCA_DUPLICADA', label: 'Fui cobrado duas vezes' },
        { value: 'COBRANCA_INDEVIDA', label: 'Cobrança após cancelamento' },
        { value: 'OUTRO', label: 'Outro problema de cobrança' }
    ],
    fraude: [
        { value: 'COMPRA_NAO_RECONHECIDA', label: 'Não reconheço essa compra' },
        { value: 'CONTA_INVADIDA', label: 'Minha conta foi invadida' }
    ],
    qualidade: [
        { value: 'COMIDA_FRIA', label: 'Comida chegou fria' },
        { value: 'COMIDA_ESTRAGADA', label: 'Comida estragada' },
        { value: 'PEDIDO_ERRADO', label: 'Não era o que pedi' },
        { value: 'OUTRO', label: 'Outro problema de qualidade' }
    ],
    atraso: [
        { value: 'ATRASO_EXCESSIVO', label: 'Atraso muito grande' },
        { value: 'TEMPO_MUITO_LONGO', label: 'Previsão de entrega ultrapassada' }
    ]
};

// Selecionar uma opção
function selectOption(element, field) {
    // Remover seleção anterior
    const container = element.parentElement;
    container.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
    
    // Adicionar seleção
    element.classList.add('selected');
    
    // Salvar no estado
    state.data[field] = element.dataset.value;
    
    // Habilitar botão de continuar
    document.getElementById('btnNext').disabled = false;
    
    // Se for categoria, atualizar motivos
    if (field === 'categoria') {
        updateMotivos(element.dataset.value);
    }
}

// Atualizar lista de motivos baseado na categoria
function updateMotivos(categoria) {
    const container = document.getElementById('motivoOptions');
    const motivos = motivosPorCategoria[categoria] || [];
    
    container.innerHTML = motivos.map(m => `
        <button class="option-item" data-value="${m.value}" onclick="selectOption(this, 'motivo')">
            <span class="option-bullet"></span>
            <span>${m.label}</span>
        </button>
    `).join('');
}

// Ir para próximo passo
function nextStep() {
    if (state.currentStep === 4) {
        // Salvar detalhes do formulário
        state.data.valorPedido = document.getElementById('valorPedido').value;
        state.data.tempoEspera = document.getElementById('tempoEspera').value;
        state.data.descricao = document.getElementById('descricaoProblema').value;
    }
    
    if (state.currentStep === 5) {
        // Enviar dados
        submitForm();
        return;
    }
    
    if (state.currentStep < state.totalSteps) {
        state.currentStep++;
        updateUI();
    }
}

// Voltar para passo anterior
function previousStep() {
    if (state.currentStep > 1) {
        state.currentStep--;
        updateUI();
    }
}

// Atualizar interface
function updateUI() {
    // Atualizar seções
    document.querySelectorAll('.form-section').forEach((section, index) => {
        section.classList.remove('active');
        if (index + 1 === state.currentStep) {
            section.classList.add('active');
        }
    });
    
    // Atualizar progress bar
    const progress = (state.currentStep / state.totalSteps) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;
    
    // Atualizar steps
    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 === state.currentStep) {
            step.classList.add('active');
        } else if (index + 1 < state.currentStep) {
            step.classList.add('completed');
        }
    });
    
    // Atualizar botões
    const btnBack = document.getElementById('btnBack');
    const btnNext = document.getElementById('btnNext');
    
    btnBack.style.display = state.currentStep > 1 ? 'block' : 'none';
    
    if (state.currentStep === 5) {
        btnNext.textContent = 'Enviar Solicitação';
        updateSummary();
        btnNext.disabled = false;
    } else if (state.currentStep === 4) {
        btnNext.textContent = 'Revisar';
        btnNext.disabled = false;
    } else {
        btnNext.textContent = 'Continuar';
        // Verificar se há seleção
        const currentField = ['categoria', 'status', 'motivo'][state.currentStep - 1];
        btnNext.disabled = !state.data[currentField];
    }
}

// Atualizar resumo
function updateSummary() {
    document.getElementById('summaryCategoria').textContent = 
        labels.categoria[state.data.categoria] || '-';
    document.getElementById('summaryStatus').textContent = 
        labels.status[state.data.status] || '-';
    document.getElementById('summaryMotivo').textContent = 
        labels.motivo[state.data.motivo] || '-';
    document.getElementById('summaryValor').textContent = 
        state.data.valorPedido ? `R$ ${parseFloat(state.data.valorPedido).toFixed(2)}` : '-';
    document.getElementById('summaryTempo').textContent = 
        state.data.tempoEspera ? `${state.data.tempoEspera} minutos` : '-';
    document.getElementById('summaryDescricao').textContent = 
        state.data.descricao || '-';
}

// Enviar formulário
function submitForm() {
    // Esconder navegação
    document.getElementById('footerNav').style.display = 'none';
    
    // Esconder step 5
    document.getElementById('step5').classList.remove('active');
    
    // Mostrar loading
    const resultSection = document.getElementById('stepResult');
    resultSection.classList.add('active');
    
    document.getElementById('resultContainer').innerHTML = `
        <div class="loading-spinner"></div>
        <p style="color: var(--medium-gray);">Analisando sua solicitação...</p>
    `;
    
    // Simular processamento (aqui você conectaria com o backend Python)
    setTimeout(() => {
        processResult();
    }, 2000);
}

// Processar resultado (simulado)
function processResult() {
    // Lógica simplificada para demonstração
    // Em produção, isso viria do backend Python
    
    let decision = 'pending';
    let title = 'Análise em andamento';
    let message = 'Sua solicitação está sendo analisada por nossa equipe.';
    let icon = '🔍';
    
    // Regras simplificadas
    if (state.data.motivo === 'CANCELAMENTO_RESTAURANTE' || 
        state.data.motivo === 'ERRO_APP' ||
        state.data.motivo === 'PEDIDO_NAO_CHEGOU') {
        decision = 'approved';
        title = 'Reembolso Aprovado!';
        message = 'Identificamos que você tem direito ao reembolso. O valor será estornado em até 7 dias úteis.';
        icon = '✅';
    } else if (state.data.motivo === 'ARREPENDIMENTO_CLIENTE' && 
               (state.data.status === 'SAIU_PARA_ENTREGA' || state.data.status === 'ENTREGUE')) {
        decision = 'rejected';
        title = 'Reembolso Não Aprovado';
        message = 'Infelizmente, não é possível reembolsar pedidos cancelados após a saída para entrega por arrependimento.';
        icon = '❌';
    } else if (state.data.categoria === 'fraude') {
        decision = 'pending';
        title = 'Análise de Segurança';
        message = 'Por motivos de segurança, sua solicitação será analisada por nossa equipe especializada. Entraremos em contato em até 48 horas.';
        icon = '🔒';
    }
    
    document.getElementById('resultContainer').innerHTML = `
        <div class="result-icon">${icon}</div>
        <h2 class="result-title ${decision}">${title}</h2>
        <p class="result-message">${message}</p>
        
        <div class="result-details">
            <div class="result-detail-item">
                <span class="result-detail-label">Protocolo</span>
                <span class="result-detail-value">#${generateProtocol()}</span>
            </div>
            <div class="result-detail-item">
                <span class="result-detail-label">Data</span>
                <span class="result-detail-value">${new Date().toLocaleDateString('pt-BR')}</span>
            </div>
            <div class="result-detail-item">
                <span class="result-detail-label">Categoria</span>
                <span class="result-detail-value">${labels.categoria[state.data.categoria]}</span>
            </div>
            <div class="result-detail-item">
                <span class="result-detail-label">Status</span>
                <span class="result-detail-value">${decision === 'approved' ? 'Aprovado' : decision === 'rejected' ? 'Negado' : 'Em análise'}</span>
            </div>
        </div>
        
        <button class="btn btn-primary" style="margin-top: 25px; width: 100%;" onclick="location.reload()">
            Nova Solicitação
        </button>
    `;
    
    // Salvar dados para possível integração com backend
    console.log('Dados da solicitação:', state.data);
    console.log('Decisão:', decision);
    
    // Aqui você pode fazer uma chamada para o backend Python
    // fetch('/api/processar', { method: 'POST', body: JSON.stringify(state.data) })
}

// Gerar número de protocolo
function generateProtocol() {
    const date = new Date();
    const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    return `${date.getFullYear()}${(date.getMonth()+1).toString().padStart(2,'0')}${date.getDate().toString().padStart(2,'0')}${random}`;
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    updateUI();
});
