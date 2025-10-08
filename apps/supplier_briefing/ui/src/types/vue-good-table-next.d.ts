declare module 'vue-good-table-next' {
  import { DefineComponent } from 'vue';

  export const VueGoodTable: DefineComponent<any, any, any>;

  const plugin: {
    install: (app: any) => void;
  };

  export default plugin;
}

declare module 'vue-good-table-next/dist/vue-good-table-next.css' {
  const content: string;
  export default content;
}
