import axios from 'axios'

export function checkHealth() {
  return axios.get('/health')
}
