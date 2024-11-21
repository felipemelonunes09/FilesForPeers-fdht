import { BadRequestException, Injectable, InternalServerErrorException } from '@nestjs/common';
import { Hashtable } from './entities/hashtable.entity';
import { ConfigService } from '@nestjs/config'
import { promises as fs } from 'fs'; 
import path from 'path';
import { CreateFileEntryDto } from './dto/create-filetableentry.dto';
import { FileTableEntry } from './entities/filetableentry.entity';

@Injectable()
export class HashtableService {
  private table: Hashtable
  
  constructor(private configService: ConfigService) {
    this.loadHashTable()
  }

  private async loadHashTable() {
    try {
      const filePath = this.configService.get("hashtableFilePath")
      this.table = new Hashtable()
      const data = await fs.readFile(filePath, 'utf-8')
      this.table = JSON.parse(data)
    }
    catch(err) {
      if (err.code === 'ENOENT') {
        console.log("Error when finding the hashtable: --resolution: creating file")
        await this.createHashTable()
      }
    }
  }

  private async createHashTable() {
    await fs.mkdir(this.configService.get("hashtableFileDir"), { recursive: true })
    this.saveHashTable()
  }

  private async saveHashTable() {
     fs.writeFile(this.configService.get("hashtableFilePath"), JSON.stringify(this.table))
  }

  async create(createFileEntryDto: CreateFileEntryDto): Promise<any> {
    const fileEntry = Object.assign(new FileTableEntry(), createFileEntryDto)
    const currentDate = new Date()
    fileEntry.createdAt = currentDate
    fileEntry.updatedAt = currentDate

    if (this.table[fileEntry.name] == undefined) {
      this.table[fileEntry.name] = fileEntry
      this.saveHashTable()
      return fileEntry
    }
    else
      return new BadRequestException("There ir already a entry with this file name")
  }

  async findAll() {
    return `This action returns all hashtable`;
  }

  async findOne(id: number) {
    return `This action returns a #${id} hashtable`;
  }

  async update(id: number, updateHashtableDto: any) {
    return `This action updates a #${id} hashtable`;
  }
  async remove(id: number) {
    return `This action removes a #${id} hashtable`;
  }
}
