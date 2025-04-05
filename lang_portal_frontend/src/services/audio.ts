import api from './api';

export const audioApi = {
    getWordAudio: async (text: string): Promise<string> => {
        const response = await api.post('/audio/synthesize/', {
            text
        }, {
            responseType: 'blob'
        });
        return URL.createObjectURL(response.data);
    }
};
