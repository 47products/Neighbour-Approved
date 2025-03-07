<template>
    <button 
      class="app-button" 
      :class="[
        `variant-${variant}`, 
        { 'loading': loading, 'block': block, 'disabled': disabled }
      ]"
      :disabled="disabled || loading"
      @click="handleClick"
    >
      <span class="loading-spinner" v-if="loading"></span>
      <span class="button-content" :class="{ 'hidden': loading }">
        <slot></slot>
      </span>
    </button>
  </template>
  
  <script>
  export default {
    name: 'AppButton',
    props: {
      variant: {
        type: String,
        default: 'primary',
        validator: (value) => ['primary', 'secondary', 'outline', 'text', 'danger'].includes(value)
      },
      loading: {
        type: Boolean,
        default: false
      },
      disabled: {
        type: Boolean,
        default: false
      },
      block: {
        type: Boolean,
        default: false
      }
    },
    setup(props, { emit }) {
      const handleClick = (event) => {
        if (!props.disabled && !props.loading) {
          emit('click', event)
        }
      }
      
      return {
        handleClick
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .app-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
    font-size: 0.875rem;
    line-height: 1.5;
    padding: $spacing-sm $spacing-md;
    border-radius: $border-radius;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    
    &.block {
      display: flex;
      width: 100%;
    }
    
    &.disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .button-content {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      
      &.hidden {
        visibility: hidden;
      }
    }
    
    .loading-spinner {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s linear infinite;
    }
    
    &.variant-primary {
      background-color: var(--color-primary);
      color: white;
      border: none;
      
      &:hover:not(.disabled) {
        background-color: var(--color-primary-dark);
      }
      
      &:active:not(.disabled) {
        background-color: var(--color-primary-darker);
      }
    }
    
    &.variant-secondary {
      background-color: var(--color-secondary);
      color: white;
      border: none;
      
      &:hover:not(.disabled) {
        background-color: var(--color-secondary-dark);
      }
      
      &:active:not(.disabled) {
        background-color: var(--color-secondary-darker);
      }
    }
    
    &.variant-outline {
      background-color: transparent;
      color: var(--color-primary);
      border: 1px solid var(--color-primary);
      
      &:hover:not(.disabled) {
        background-color: var(--color-primary-light);
      }
      
      &:active:not(.disabled) {
        background-color: var(--color-primary-lighter);
      }
      
      .loading-spinner {
        border: 2px solid rgba(var(--color-primary-rgb), 0.3);
        border-top-color: var(--color-primary);
      }
    }
    
    &.variant-text {
      background-color: transparent;
      color: var(--color-primary);
      border: none;
      padding: $spacing-xs $spacing-sm;
      
      &:hover:not(.disabled) {
        background-color: var(--color-primary-light);
      }
      
      &:active:not(.disabled) {
        background-color: var(--color-primary-lighter);
      }
      
      .loading-spinner {
        border: 2px solid rgba(var(--color-primary-rgb), 0.3);
        border-top-color: var(--color-primary);
      }
    }
    
    &.variant-danger {
      background-color: var(--color-error);
      color: white;
      border: none;
      
      &:hover:not(.disabled) {
        background-color: var(--color-error-dark);
      }
      
      &:active:not(.disabled) {
        background-color: var(--color-error-darker);
      }
    }
  }
  
  @keyframes spin {
    to {
      transform: translate(-50%, -50%) rotate(360deg);
    }
  }
  </style>