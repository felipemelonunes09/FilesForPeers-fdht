import { IsNumber, isNumber, IsObject, IsOptional, IsString } from "class-validator";


export class UpdateFileEntryDto {

    @IsOptional()
    @IsString()
    name?: string
    
    @IsOptional()
    @IsString()
    path?: string

    @IsOptional()
    @IsNumber()
    size?: number
}
