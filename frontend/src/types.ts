export type Field={name:string;label?:string;type?:'text'|'date'|'month'|'number'|'select'|'textarea';options?:string[];required?:boolean;section?:string};
export type Module={id:string;label:string;description:string;fields:Field[];status?:boolean};
