import { useState, useCallback } from 'react';
import { InputValidator, type ValidationResult } from '@/utils/validation';

export interface ValidationState {
  [key: string]: {
    isValid: boolean;
    errors: string[];
    touched: boolean;
  };
}

export function useValidation(initialState: Record<string, string> = {}) {
  const [validationState, setValidationState] = useState<ValidationState>(() => {
    const initial: ValidationState = {};
    Object.keys(initialState).forEach(key => {
      initial[key] = {
        isValid: true,
        errors: [],
        touched: false,
      };
    });
    return initial;
  });

  const validateField = useCallback((fieldName: string, value: string): ValidationResult => {
    let result: ValidationResult;

    switch (fieldName) {
      case 'message':
        result = InputValidator.validateMessage(value);
        break;
      case 'apiKey':
        result = InputValidator.validateApiKey(value);
        break;
      case 'threadId':
        result = InputValidator.validateThreadId(value);
        break;
      case 'modelName':
        result = InputValidator.validateModelName(value);
        break;
      default:
        result = {
          isValid: true,
          errors: [],
          sanitizedValue: InputValidator.sanitizeInput(value),
        };
    }

    setValidationState(prev => ({
      ...prev,
      [fieldName]: {
        isValid: result.isValid,
        errors: result.errors,
        touched: true,
      },
    }));

    return result;
  }, []);

  const validateAllFields = useCallback((data: Record<string, string>) => {
    const results = InputValidator.validateForm(data);
    const newValidationState: ValidationState = {};

    Object.entries(results).forEach(([key, result]) => {
      newValidationState[key] = {
        isValid: result.isValid,
        errors: result.errors,
        touched: true,
      };
    });

    setValidationState(newValidationState);
    return results;
  }, []);

  const clearValidation = useCallback((fieldName?: string) => {
    if (fieldName) {
      setValidationState(prev => ({
        ...prev,
        [fieldName]: {
          isValid: true,
          errors: [],
          touched: false,
        },
      }));
    } else {
      setValidationState({});
    }
  }, []);

  const isFormValid = useCallback(() => {
    return Object.values(validationState).every(field => field.isValid);
  }, [validationState]);

  const getFieldError = useCallback((fieldName: string) => {
    const field = validationState[fieldName];
    return field?.touched && !field.isValid ? field.errors[0] : null;
  }, [validationState]);

  const hasFieldError = useCallback((fieldName: string) => {
    const field = validationState[fieldName];
    return field?.touched && !field.isValid;
  }, [validationState]);

  return {
    validationState,
    validateField,
    validateAllFields,
    clearValidation,
    isFormValid,
    getFieldError,
    hasFieldError,
  };
}