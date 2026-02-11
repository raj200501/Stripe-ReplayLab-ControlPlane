import js from '@eslint/js'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'

export default [
  js.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: { parser: tsparser },
    plugins: { '@typescript-eslint': tseslint },
    rules: { 'no-undef': 'off' }
  }
]
