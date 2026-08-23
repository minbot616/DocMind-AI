/* DocMind AI - REST API Client Module (Multi-View Single-User Workspace) */

const API_BASE = "";

class ApiClient {
  static async request(endpoint, options = {}) {
    const headers = options.headers || {};
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, config);
      if (response.status === 204) {
        return null;
      }
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.error?.message || `HTTP ${response.status} Error`);
      }
      return data;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // Document Endpoints
  static async getDocuments() {
    return await this.request("/documents");
  }

  static async getDocument(docId) {
    return await this.request(`/documents/${docId}`);
  }

  static async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);
    return await this.request("/documents/upload", {
      method: "POST",
      body: formData
    });
  }

  static async uploadMultipleDocuments(files) {
    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }
    return await this.request("/documents/upload-multiple", {
      method: "POST",
      body: formData
    });
  }

  static async deleteDocument(docId) {
    return await this.request(`/documents/${docId}`, {
      method: "DELETE"
    });
  }

  // Conversation & Chat Endpoints
  static async getConversations() {
    return await this.request("/conversations");
  }

  static async getConversation(chatId) {
    return await this.request(`/conversations/${chatId}`);
  }

  static async createConversation(title = "New Conversation") {
    return await this.request("/conversations", {
      method: "POST",
      body: JSON.stringify({ title })
    });
  }

  static async deleteConversation(chatId) {
    return await this.request(`/conversations/${chatId}`, {
      method: "DELETE"
    });
  }

  static async sendChatMessage(chatId, message, selectedDocIds = null) {
    return await this.request("/chat", {
      method: "POST",
      body: JSON.stringify({
        conversation_id: chatId,
        message: message,
        selected_doc_ids: selectedDocIds && selectedDocIds.length > 0 ? selectedDocIds : null
      })
    });
  }

  // Settings Endpoints
  static async getSettings() {
    return await this.request("/settings");
  }

  static async updateSettings(settings) {
    return await this.request("/settings", {
      method: "POST",
      body: JSON.stringify(settings)
    });
  }

  static async getProviderModels(provider) {
    return await this.request(`/settings/models?provider=${encodeURIComponent(provider)}`);
  }

  static async getHealth() {
    return await this.request("/health");
  }

  static async testConnection(payload) {
    return await this.request("/settings/test-connection", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }
}

window.ApiClient = ApiClient;
