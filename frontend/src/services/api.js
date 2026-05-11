/**
 * API Service para integração com o backend FastAPI
 * Usa import.meta.env.VITE_API_BASE_URL para configurar a URL base
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Função genérica para fazer requisições GET à API
 * @param {string} path - Caminho da rota (ex: '/api/v1/customers')
 * @param {object} options - Opções adicionais (headers, params, etc)
 * @returns {Promise} Resposta da API em JSON
 * @throws {Error} Se a resposta não for OK ou se houver erro de rede
 */
export async function apiGet(path, options = {}) {
  try {
    const url = new URL(`${API_BASE_URL}${path}`);
    
    // Adicionar query params se fornecidos
    if (options.params) {
      Object.keys(options.params).forEach(key => {
        url.searchParams.append(key, options.params[key]);
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`API Error: ${response.status} - ${response.statusText} - ${errorData.detail || ''}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API GET Error [${path}]:`, error);
    throw error;
  }
}

/**
 * Função genérica para fazer requisições POST à API
 * @param {string} path - Caminho da rota
 * @param {object} data - Dados a enviar no corpo da requisição
 * @param {object} options - Opções adicionais
 * @returns {Promise} Resposta da API em JSON
 * @throws {Error} Se a resposta não for OK
 */
export async function apiPost(path, data = {}, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`API Error: ${response.status} - ${response.statusText} - ${errorData.detail || ''}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API POST Error [${path}]:`, error);
    throw error;
  }
}

export default {
  apiGet,
  apiPost
};
