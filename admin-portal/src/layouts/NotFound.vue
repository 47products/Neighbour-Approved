<template>
    <div class="not-found">
      <div class="not-found-content">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The page you're looking for doesn't exist or has been moved.</p>
        <AppButton @click="goHome">Back to Dashboard</AppButton>
      </div>
    </div>
  </template>
  
  <script>
  import { useRouter } from 'vue-router'
  import AppButton from '@/components/common/AppButton.vue'
  
  export default {
    name: 'NotFound',
    components: {
      AppButton
    },
    setup() {
      const router = useRouter()
      
      const goHome = () => {
        router.push({ name: 'Dashboard' })
      }
      
      return {
        goHome
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .not-found {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 80vh;
    text-align: center;
    
    .not-found-content {
      max-width: 400px;
      padding: $spacing-lg;
      
      h1 {
        font-size: 8rem;
        margin: 0;
        color: var(--color-primary);
        line-height: 1;
      }
      
      h2 {
        margin-top: $spacing-sm;
        margin-bottom: $spacing-md;
        color: var(--color-text-primary);
      }
      
      p {
        margin-bottom: $spacing-lg;
        color: var(--color-text-secondary);
      }
    }
  }
  </style>